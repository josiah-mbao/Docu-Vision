from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage
import os

app = FastAPI()

# Serve static files (frontend)
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

# Allow CORS for frontend JS fetch
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup GCP bucket
bucket_name = "docu-vision-bucket-juice"
storage_client = storage.Client()

@app.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    try:
        os.makedirs("temp", exist_ok=True)
        file_location = f"temp/{file.filename}"

        with open(file_location, "wb") as f:
            f.write(await file.read())

        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file.filename)
        blob.upload_from_filename(file_location)

        return JSONResponse(content={"message": "Document uploaded successfully!"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

