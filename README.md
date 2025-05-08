# Docu Vision
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)](https://cloud.google.com/)
[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![Cloud Functions](https://img.shields.io/badge/GCP%20Cloud%20Functions-7956E6?style=for-the-badge&logo=googlecloud&logoColor=white)](https://cloud.google.com/functions)

**A document intelligence API** I've created to process documents and extract structured data using Google's Document AI API. This SaaS helps automate document processing tasks like invoice extraction, form filling, and more.
<img width="1552" alt="Screenshot 2025-05-08 at 20 27 49" src="https://github.com/user-attachments/assets/e44b167c-1a62-4298-9a15-8d45b89460f6" />


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

