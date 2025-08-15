"""DocuVision - AI Document Processing API with Authentication"""
import os
import json
import logging
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List

import httpx
import asyncpg
from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
    BackgroundTasks,
    Depends,
    status,
    Request,
    Query,
    Form
)
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt

# Load environment variables from project root
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Configuration
class Settings(BaseModel):
    app_name: str = "DocuVision"
    version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: List[str] = ["image/jpeg", "image/png", "application/pdf"]
    temp_dir: str = "temp"
    openrouter_model: str = "mistralai/mistral-7b-instruct"
    openrouter_temperature: float = 0.5
    database_url: str = os.getenv("DATABASE_URL")
    require_api_key: bool = os.getenv("REQUIRE_API_KEY", "false").lower() == "true"
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30

# Initialize settings
settings = Settings()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("docuvision.log")
    ]
)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Initialize FastAPI
app = FastAPI(
    title=settings.app_name,
    description="AI-powered document processing with OCR and NLP",
    version=settings.version,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Security
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class DocumentAnalysisResult(BaseModel):
    document_type: str = Field(..., description="Detected document type")
    summary: str = Field(..., description="AI-generated summary")
    extracted_data: Dict[str, Any] = Field(default_factory=dict, description="Structured extracted data")

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Auth Models
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: str
    hashed_password: str
    is_active: bool = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Document Models
class DocumentCreate(BaseModel):
    user_id: str
    filename: str
    ocr_text: str
    analysis: Optional[Dict[str, Any]] = None

class DocumentResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    ocr_text: str
    analysis: Optional[Dict[str, Any]] = None
    created_at: datetime

# Database Connection Pool
async def get_db_pool():
    return await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=1,
        max_size=10,
        command_timeout=60
    )

@app.on_event("startup")
async def startup_event():
    app.state.db_pool = await get_db_pool()
    await initialize_database()

@app.on_event("shutdown")
async def shutdown_event():
    await app.state.db_pool.close()

async def initialize_database():
    """Create tables if they don't exist"""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
    );
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        user_id TEXT REFERENCES users(id),
        filename TEXT NOT NULL,
        ocr_text TEXT NOT NULL,
        analysis JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
    );
    CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
    CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
    """
    
    try:
        async with app.state.db_pool.acquire() as conn:
            await conn.execute(create_table_sql)
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

# Dependency
async def get_db_conn():
    async with app.state.db_pool.acquire() as conn:
        yield conn

# Auth Utilities
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt_secret_key, 
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    conn=Depends(get_db_conn)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = await conn.fetchrow(
        "SELECT * FROM users WHERE email = $1",
        token_data.email
    )
    if user is None:
        raise credentials_exception
    return UserInDB(**user)

# Utility functions
def get_api_key(api_key: str = Depends(api_key_header)) -> str:
    """Validate API key if required"""
    if settings.require_api_key:
        if not api_key or api_key != os.getenv("API_KEY"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API Key"
            )
    return api_key

async def validate_file(file: UploadFile):
    """Validate uploaded file"""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file uploaded"
        )
    
    if file.content_type not in settings.allowed_file_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed types: {', '.join(settings.allowed_file_types)}"
        )
    
    file_size = 0
    for chunk in file.file:
        file_size += len(chunk)
        if file_size > settings.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max size: {settings.max_file_size/1024/1024}MB"
            )
    
    file.file.seek(0)
    return file

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(APIResponse(
            success=False,
            message="Error occurred",
            error=exc.detail
        ))
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(APIResponse(
            success=False,
            message="Validation error",
            error=exc.errors()
        ))
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(APIResponse(
            success=False,
            message="Internal server error",
            error="An unexpected error occurred"
        ))
    )

# Database operations
async def create_document(conn, document: DocumentCreate) -> str:
    """Insert a new document record"""
    doc_id = str(uuid.uuid4())
    await conn.execute(
        """
        INSERT INTO documents (id, user_id, filename, ocr_text, analysis)
        VALUES ($1, $2, $3, $4, $5)
        """,
        doc_id,
        document.user_id,
        document.filename,
        document.ocr_text,
        json.dumps(document.analysis) if document.analysis else None
    )
    return doc_id

async def get_document(conn, doc_id: str, user_id: str) -> Optional[DocumentResponse]:
    """Retrieve a single document for a specific user"""
    record = await conn.fetchrow(
        "SELECT * FROM documents WHERE id = $1 AND user_id = $2",
        doc_id, user_id
    )
    if record:
        return DocumentResponse(
            id=record['id'],
            user_id=record['user_id'],
            filename=record['filename'],
            ocr_text=record['ocr_text'],
            analysis=record['analysis'],
            created_at=record['created_at']
        )
    return None

async def list_documents(
    conn,
    user_id: str,
    limit: int = 10,
    offset: int = 0
) -> List[DocumentResponse]:
    """List documents for a specific user with pagination"""
    records = await conn.fetch(
        """
        SELECT * FROM documents
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
        """,
        user_id, limit, offset
    )
    return [
        DocumentResponse(
            id=record['id'],
            user_id=record['user_id'],
            filename=record['filename'],
            ocr_text=record['ocr_text'],
            analysis=record['analysis'],
            created_at=record['created_at']
        )
        for record in records
    ]

# Auth Endpoints
@app.post("/api/auth/register/", response_model=UserBase)
async def register_user(
    email: str = Form(...),
    password: str = Form(...),
    conn=Depends(get_db_conn)
):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = await conn.fetchrow(
            "SELECT * FROM users WHERE email = $1",
            email
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(password)
        
        await conn.execute(
            """
            INSERT INTO users (id, email, hashed_password)
            VALUES ($1, $2, $3)
            """,
            user_id,
            email,
            hashed_password
        )
        
        return {"email": email}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during registration"
        )

@app.post("/api/auth/login/", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    conn=Depends(get_db_conn)
):
    """Authenticate user and return JWT token"""
    user = await conn.fetchrow(
        "SELECT * FROM users WHERE email = $1",
        form_data.username
    )
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.jwt_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["email"]}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me/", response_model=UserBase)
async def read_users_me(
    current_user: UserInDB = Depends(get_current_user)
):
    """Get current user info"""
    return current_user

# Document Endpoints
@app.post("/api/documents/", response_model=APIResponse)
@limiter.limit("10/minute")
async def create_document_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = Depends(validate_file),
    current_user: UserInDB = Depends(get_current_user),
    conn=Depends(get_db_conn),
    ocr_api_key: Optional[str] = None
):
    """Process and store document for authenticated user"""
    try:
        # Create temp directory if not exists
        os.makedirs(settings.temp_dir, exist_ok=True)
        file_extension = Path(file.filename).suffix
        file_location = f"{settings.temp_dir}/{uuid.uuid4()}{file_extension}"

        # Save the file locally
        with open(file_location, "wb") as out_file:
            for chunk in file.file:
                out_file.write(chunk)

        # Schedule file cleanup
        background_tasks.add_task(cleanup_file, file_location)

        # Process with OCR
        api_key = ocr_api_key or os.getenv("OCR_API_KEY", "helloworld")
        extracted_text = await ocr_space_extract(file_location, api_key)

        # Optional AI analysis
        analysis_result = None
        if openrouter_api_key := os.getenv("OPENROUTER_API_KEY"):
            analysis_result = await analyze_document_with_openrouter(
                extracted_text, openrouter_api_key)

        # Store in database
        doc_id = await create_document(
            conn,
            DocumentCreate(
                user_id=current_user.id,
                filename=file.filename,
                ocr_text=extracted_text,
                analysis=analysis_result.dict() if analysis_result else None
            )
        )

        return APIResponse(
            success=True,
            message="Document processed and stored",
            data={
                "document_id": doc_id,
                "filename": file.filename,
                "ocr_text": extracted_text,
                "analysis": analysis_result
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document processing error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing document"
        )

@app.get("/api/documents/", response_model=List[DocumentResponse])
@limiter.limit("60/minute")
async def list_documents_endpoint(
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
    limit: int = Query(10, gt=0, le=100),
    offset: int = Query(0, ge=0),
    conn=Depends(get_db_conn)
):
    """List documents for current user"""
    return await list_documents(conn, current_user.id, limit, offset)

@app.get("/api/documents/{doc_id}", response_model=DocumentResponse)
@limiter.limit("60/minute")
async def get_document_endpoint(
    request: Request,
    doc_id: str,
    current_user: UserInDB = Depends(get_current_user),
    conn=Depends(get_db_conn)
):
    """Retrieve a specific document for current user"""
    document = await get_document(conn, doc_id, current_user.id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return document

# Helper functions
async def ocr_space_extract(file_path: str, api_key: str) -> str:
    """Extract text using OCR.space API"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.ocr.space/parse/image",
                files={"file": open(file_path, "rb")},
                data={
                    "apikey": api_key,
                    "language": "eng",
                    "isOverlayRequired": False,
                    "OCREngine": 2  # More accurate engine
                },
            )
            response.raise_for_status()
            data = response.json()

            if data.get("IsErroredOnProcessing", False):
                error_msg = data.get("ErrorMessage", "Unknown OCR error")
                logger.error(f"OCR.space error: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"OCR error: {error_msg}"
                )

            if not data.get("ParsedResults"):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="No text detected in document"
                )

            return data["ParsedResults"][0]["ParsedText"]

    except httpx.HTTPStatusError as e:
        logger.error(f"OCR API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OCR service unavailable"
        )
    except httpx.TimeoutException:
        logger.error("OCR API timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="OCR service timeout"
        )

async def analyze_document_with_openrouter(ocr_text: str, api_key: str) -> DocumentAnalysisResult:
    """Analyze document using OpenRouter API"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://docuvision.example.com",
        "X-Title": "DocuVision"
    }

    prompt = f"""
You are an intelligent document processing assistant. Analyze this document:

1. Determine document type (invoice, receipt, resume, letter, email, ID, other)
2. Provide a concise summary
3. Extract relevant structured data based on type

Respond in this JSON format:
{{
  "document_type": "...",
  "summary": "...",
  "extracted_data": {{
    // key-value pairs
  }}
}}

Document text:
\"\"\"{ocr_text}\"\"\"
"""

    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": "You analyze documents professionally."},
            {"role": "user", "content": prompt}
        ],
        "temperature": settings.openrouter_temperature,
        "response_format": {"type": "json_object"}
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            raw_output = data["choices"][0]["message"]["content"]

            try:
                result = json.loads(raw_output)
                return DocumentAnalysisResult(**result)
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Invalid JSON from AI: {raw_output}")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="AI returned invalid response format"
                )

    except httpx.HTTPStatusError as e:
        logger.error(f"OpenRouter API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI analysis service unavailable"
        )

def cleanup_file(file_path: str):
    """Delete temporary file with error handling"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Deleted temp file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to delete temp file {file_path}: {e}")

# Static files and frontend
FRONTEND_INDEX = BASE_DIR.parent.parent / "frontend" / "index.html"
STATIC_DIR = (BASE_DIR.parent.parent / "frontend").resolve()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def serve_home(request: Request):
    try:
        with open(FRONTEND_INDEX, "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        logger.error(f"Error serving frontend: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load frontend"
        )
