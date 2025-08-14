# DocuVision 🧠📄 - AI Document Processing

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-1E1E2D?style=for-the-badge&logo=openai&logoColor=white)](https://openrouter.ai)
[![PWA](https://img.shields.io/badge/PWA-5A0FC8?style=for-the-badge&logo=pwa&logoColor=white)](https://web.dev/progressive-web-apps/)
[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

---

![DocuVision Screenshot](https://github.com/user-attachments/assets/497c3d82-f396-4d54-92c3-5df37fc0e249)

---

## 📄 About

**DocuVision** is an AI-powered document processing system that combines OCR extraction with intelligent document analysis. It uses **OCR.space** for text extraction and **OpenRouter AI** for document understanding, classification, and data structuring. The application is built with production-ready practices including rate limiting, API security, and PWA support.

Key Improvements:
- 🛡️ Added API security and rate limiting
- 📱 Enhanced mobile experience with PWA support
- 🧠 Smarter document analysis with AI classification
- ⚡ Optimized performance with GZip compression
- 🎨 Improved UI/UX with better feedback systems

---

## 🧠 Core Features

### Document Processing
- 📤 **Multi-format Upload**: Supports PDFs, JPEG, PNG (up to 10MB)
- 🔍 **Advanced OCR**: OCR.space integration with fallback handling
- 🧠 **AI Analysis**: Document classification and data extraction via OpenRouter
- 📊 **Structured Output**: Clean JSON responses with typed fields

### Technical Features
- ⚡ **Production-Ready API**: Rate limiting, error handling, and docs
- 🔒 **Optional API Key Security**: Protect your endpoints
- 📱 **PWA Support**: Installable and works offline
- 📈 **Progress Tracking**: Real-time upload and processing feedback
- 🖨️ **Print Styles**: Document-friendly print output

### Developer Experience
- 📝 **Swagger Docs**: Interactive API documentation at `/api/docs`
- 🔍 **Validation**: Strict file type and size validation
- 🧩 **Modular Design**: Clean separation of concerns
- 📊 **Logging**: Comprehensive request and error logging

---

## 🌐 Enhanced Tech Stack

| Component          | Technology                                                                 |
|--------------------|---------------------------------------------------------------------------|
| **Frontend**       | HTML5, CSS3, JavaScript (PWA-enabled)                                    |
| **Backend**        | FastAPI (Python) with Pydantic models                                    |
| **OCR**           | OCR.space API                                                            |
| **AI Analysis**    | OpenRouter AI (Mistral 7B)                                               |
| **Security**       | API Key Auth, Rate Limiting                                              |
| **Performance**    | GZip Middleware, Async Processing                                       |
| **DevOps**         | Logging, Error Tracking, Configuration Management                       |

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.9+
- Node.js (for optional frontend builds)
- API keys for:
  - OCR.space (free tier available)
  - OpenRouter (optional)

### Installation
```bash
# Clone the repository
git clone https://github.com/josiah-mbao/docuvision.git
cd docuvision

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys