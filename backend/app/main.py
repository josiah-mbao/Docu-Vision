""" This is the FastAPI backend
"""
import os
from typing import Optional
import logging
from pathlib import Path
import httpx
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Ensure the base directory is set correctly
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_INDEX = BASE_DIR.parent.parent / "frontend" / "index.html"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Serve frontend at a dedicated path like /static
STATIC_DIR = (BASE_DIR.parent.parent / "frontend").resolve()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# Serve index.html manually at "/"
@app.get("/", response_class=HTMLResponse)
async def serve_home():
    with open(FRONTEND_INDEX, "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def ocr_space_extract(file_path: str, api_key: str = "helloworld") -> str:
    """
    Extract text from an image/file using OCR.space API
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.ocr.space/parse/image",
                files={"file": open(file_path, "rb")},
                data={
                    "apikey": api_key,
                    "language": "eng",
                    "isOverlayRequired": False
                },
            )
            response.raise_for_status()
            data = response.json()

            if data.get("IsErroredOnProcessing", False):
                error_msg = data.get("ErrorMessage", "Unknown OCR error")
                logger.error(f"OCR.space error: {error_msg}")
                raise ValueError(error_msg)

            if not data.get("ParsedResults"):
                raise ValueError("No text detected in document")

            return data["ParsedResults"][0]["ParsedText"]

    except httpx.HTTPStatusError as e:
        logger.error(f"OCR.space API error: {e}")
        raise HTTPException(status_code=502, detail="OCR API unavailable")
    except (IndexError, KeyError, ValueError) as e:
        logger.error(f"OCR processing error: {e}")
        raise HTTPException(status_code=422, detail=str(e))


def cleanup_file(file_path: str):
    """Delete temporary file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.warning(f"Failed to delete temp file {file_path}: {e}")


@app.post("/upload/")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    ocr_api_key: Optional[str] = None
):
    """ File-upload endpoint"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")

        # Ensure the temp folder exists
        os.makedirs("temp", exist_ok=True)
        file_location = f"temp/{file.filename}"

        # Save the file locally
        with open(file_location, "wb") as out_file:
            out_file.write(await file.read())

        # Schedule file cleanup after request completes
        background_tasks.add_task(cleanup_file, file_location)

        # Process with OCR.space
        api_key = ocr_api_key or "helloworld"  # Default to free public key
        extracted_text = await ocr_space_extract(file_location, api_key)

        # Optional: Summarize using OpenRouter
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        summary = None
        if openrouter_api_key:
            summary = await summarize_with_openrouter(
                extracted_text, openrouter_api_key)

        return JSONResponse(
            content={
                "message": "Document processed successfully!",
                "text": extracted_text,
                "summary": summary,
                "filename": file.filename
            }
        )

    except HTTPException:
        raise  # Re-raise already handled exceptions
    except Exception as e:
        logger.error(f"Unexpected error during document processing: {e}")
        raise HTTPException(
            status_code=500,
            detail=f'Error processing document: {str(e)}'
        ) from e


@app.post("/process/")
async def process_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    ocr_api_key: Optional[str] = None
):
    """Alternative endpoint that just processes without upload semantics"""
    return await upload_document(background_tasks, file, ocr_api_key)


async def summarize_with_openrouter(ocr_text: str, openrouter_api_key: str) -> str:
    """
    Send OCR text to OpenRouter API for summarization or Q&A
    """
    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "openai/gpt-3.5-turbo",  # You can replace with other models
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes documents."
            },
            {
                "role": "user",
                "content": f"Please summarize the following document:\n\n{ocr_text}"
            }
        ],
        "temperature": 0.7
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        logger.error(f"OpenRouter API error: {e}")
        raise HTTPException(status_code=502, detail="OpenRouter API error")
    except Exception as e:
        logger.error(f"Error summarizing document: {e}")
        raise HTTPException(status_code=500, detail="Failed to summarize text")
