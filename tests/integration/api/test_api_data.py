import pytest
import io

def test_api_ocr_upload(client, mock_openai, monkeypatch):
    # Setup
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    mock_openai.return_value = "Mocked OCR Result"
    
    # Execute
    files = {"file": ("resume.pdf", io.BytesIO(b"%PDF-1.4 dummy"), "application/pdf")}
    resp = client.post("/api/data/ocr", files=files)
    
    # Assert
    assert resp.status_code == 200
    assert resp.json()["text"] == "Mocked OCR Result"

def test_api_ocr_unsupported_file(client):
    # Execute
    files = {"file": ("resume.exe", io.BytesIO(b"binary"), "application/octet-stream")}
    resp = client.post("/api/data/ocr", files=files)
    
    # Assert
    assert resp.status_code == 400
    assert "Unsupported file type" in resp.json()["detail"]
