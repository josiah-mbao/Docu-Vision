"""DocuVision - AI Document Processing API"""
import os
import json
import logging
import uuid
from pathlib import Path
from typing import Optional, Dict, Any

import httpx
from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
    BackgroundTasks,
    Depends,
    status,
    Request
)
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import APIKeyHeader
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

# Configuration
class Settings(BaseModel):
    app_name: str = "DocuVision"
    version: str = "1.0.0"
    debug: bool = False
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list = ["image/jpeg", "image/png", "application/pdf"]
    temp_dir: str = "temp"
    openrouter_model: str = "mistralai/mistral-7b-instruct"
    openrouter_temperature: float = 0.5

# Load environment variables from project root
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize settings
settings = Settings(
    debug=os.getenv("DEBUG", "false").lower() == "true"
)

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
    allow_methods=["GET", "POST"],
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

# Utility functions
def get_api_key(api_key: str = Depends(api_key_header)) -> str:
    """Validate API key if required"""
    if os.getenv("REQUIRE_API_KEY", "false").lower() == "true":
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

# API Endpoints
@app.post("/api/upload/", response_model=APIResponse)
@limiter.limit("10/minute")
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = Depends(validate_file),
    ocr_api_key: Optional[str] = None,
    api_key: str = Depends(get_api_key)
):
    """Process uploaded document with OCR and AI analysis"""
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

        return APIResponse(
            success=True,
            message="Document processed successfully",
            data={
                "ocr_text": extracted_text,
                "analysis": analysis_result,
                "filename": file.filename
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
        "HTTP-Referer": "https://docuvision.example.com",  # Required by OpenRouter
        "X-Title": "DocuVision"  # Identify your app
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