import os
import pytest
from fastapi.testclient import TestClient
from fastapi import status
from app.main import app

client = TestClient(app)

def test_home_serves_index(monkeypatch):
    # Mock the index.html file
    index_path = app.extra["static"].directory / "index.html"
    monkeypatch.setattr("builtins.open", lambda f, mode="r": open(__file__, "r"))
    response = client.get("/")
    assert response.status_code == 200
    assert "def test_home_serves_index" in response.text

def test_upload_no_file():
    response = client.post("/upload/", files={})
    assert response.status_code == 400
    assert "No file uploaded" in response.text

def test_upload_invalid_file(monkeypatch):
    # Mock OCR function to avoid real API call
    monkeypatch.setattr("app.main.ocr_space_extract", lambda *a, **kw: "mocked text")
    file_content = b"fake image content"
    files = {"file": ("test.png", file_content, "image/png")}
    response = client.post("/upload/", files=files)
    assert response.status_code == 200
    assert "Document processed successfully" in response.text

def test_process_document(monkeypatch):
    # Mock OCR function to avoid real API call
    monkeypatch.setattr("app.main.ocr_space_extract", lambda *a, **kw: "mocked text")
    file_content = b"fake image content"
    files = {"file": ("test2.png", file_content, "image/png")}
    response = client.post("/process/", files=files)
    assert response.status_code == 200
    assert "Document processed successfully" in response.text
