from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage
from fastapi.responses import HTMLResponse
import os

app = FastAPI()

# Serve frontend at a dedicated path like /static
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# Serve index.html manually at "/"
@app.get("/", response_class=HTMLResponse)
async def serve_home():
    with open("../frontend/index.html") as f:
        return f.read()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup GCP
bucket_name = "docu-vision-bucket-juice"
storage_client = storage.Client()

@app.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    try:
        # Ensure the temp folder exists
        os.makedirs("temp", exist_ok=True)

        # File location
        file_location = f"temp/{file.filename}"

        # Save the file locally
        with open(file_location, "wb") as out_file:
            out_file.write(await file.read())

        # Upload to Google Cloud Storage
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file.filename)
        blob.upload_from_filename(file_location)

        # Clean up (delete the local file after upload)
        os.remove(file_location)

        return JSONResponse(content={"message": "Document uploaded successfully!"})

    except Exception as e:
        # Print the error in the server logs for debugging
        print(f"Error during file upload: {e}")

        # Return a more specific error message
        return JSONResponse(
            status_code=500,
            content={"message": f"Error uploading document: {str(e)}"}
        )
