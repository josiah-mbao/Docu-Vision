# Document Intelligence API

**Ona Vision**: An API to process documents and extract structured data using Google's Document AI API. This SaaS helps automate document processing tasks like invoice extraction, form filling, and more.

## 🧠 Core Features

- **Document Upload**: Users can upload documents (PDFs, images) via the web interface or API.
- **OCR + Data Extraction**: Uses Google Document AI API to extract structured data from documents.
- **Real-time Data**: Provides the extracted data in a clean JSON format for easy integration into any system.
- **Web Interface**: A simple, intuitive frontend built with React.js that allows users to upload documents and view results.
- **REST API**: Expose endpoints to upload documents and retrieve processed data in JSON format.

## 🌐 Tech Stack

- **Frontend**: React.js, TailwindCSS, Firebase Hosting
- **Backend/API**: FastAPI (Python), Google Cloud Run
- **Cloud Functions**: GCP Cloud Functions for handling document processing
- **File Storage**: Google Cloud Storage (GCS)
- **Data Storage**: Firestore (for storing processed document data)
- **Document Parsing**: Google Document AI API for OCR and data extraction
- **Authentication**: Firebase Auth for user management
- **Monitoring & Analytics**: Google Cloud Monitoring, Firebase Analytics

## ⚙️ Setting Up the Project Locally

### 1. Clone the Repository

```bash
git clone https://github.com/josiah-mbao/document-intelligence-api.git
cd document-intelligence-api

