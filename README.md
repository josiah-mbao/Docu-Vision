# Docu Vision 🧠📄

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)](https://cloud.google.com/)
[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![Cloud Functions](https://img.shields.io/badge/GCP%20Cloud%20Functions-7956E6?style=for-the-badge&logo=googlecloud&logoColor=white)](https://cloud.google.com/functions)

---

<img width="1552" alt="Screenshot 2025-05-08 at 20 27 49" src="https://github.com/user-attachments/assets/e44b167c-1a62-4298-9a15-8d45b89460f6" />

---

## 📄 About

**Docu Vision** is a lightweight document intelligence API that extracts structured data from scanned documents using **Google's Document AI**. It is ideal for automating tasks like invoice parsing, form digitization, and general OCR-powered processing.

---

## 🧠 Core Features

- 📤 **Document Upload**: Upload PDFs and images via a simple frontend or REST API.
- 🔎 **OCR + Data Extraction**: Uses Google Document AI for accurate text parsing and structuring.
- ⚡ **Real-Time Output**: JSON results returned for easy backend consumption.
- 🖥️ **Web Interface**: Simple, responsive HTML/JS frontend served via FastAPI.
- 🔁 **Event-driven Processing**: GCP Cloud Function auto-triggers on file upload to GCS.

---

## 🌐 Tech Stack

| Layer        | Tech Used                                                                 |
|--------------|---------------------------------------------------------------------------|
| **Frontend** | HTML5, CSS3, JavaScript                                                   |
| **Backend**  | FastAPI (Python)                                                          |
| **File Storage** | Google Cloud Storage (GCS)                                            |
| **Processing** | Google Cloud Function + Document AI                                     |
| **Authentication** (optional) | Firebase Auth                                            |
| **Hosting** | FastAPI (locally or via GCP Cloud Run / Functions Framework)              |

---

## ⚙️ Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/josiah-mbao/document-intelligence-api.git
cd document-intelligence-api

# 2. (Optional) Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# 3. Install backend dependencies
pip install -r requirements.txt

# 4. Run the FastAPI server
uvicorn main:app --reload
