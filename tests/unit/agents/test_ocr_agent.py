import pytest
from pathlib import Path
from agents.ocr_agent import (
    is_supported_suffix,
    extract_resume_text_from_path,
    extract_and_arrange_resume_from_path
)

def test_is_supported_suffix():
    assert is_supported_suffix("resume.pdf") is True
    assert is_supported_suffix("photo.jpg") is True
    assert is_supported_suffix("doc.txt") is False

def test_extract_resume_text_from_path(mock_openai, tmp_path, monkeypatch):
    # Setup
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    dummy_file = tmp_path / "resume.pdf"
    dummy_file.write_bytes(b"%PDF-1.4 dummy")
    
    mock_openai.return_value = "Mocked OCR Text"
    
    # Execute
    text = extract_resume_text_from_path(dummy_file)
    
    # Assert
    assert text == "Mocked OCR Text"
    assert mock_openai.called

def test_extract_and_arrange_resume_from_path(mock_openai, tmp_path, monkeypatch):
    # Setup
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    dummy_file = tmp_path / "resume.png"
    dummy_file.write_bytes(b"dummy image")
    
    import json
    mock_payload = {
        "ocr_text": "Extracted Markdown",
        "arranged_profile": {
            "candidate_name": "Jane Doe",
            "experience": []
        }
    }
    mock_openai.return_value = json.dumps(mock_payload)
    
    # Execute
    result = extract_and_arrange_resume_from_path(dummy_file)
    
    # Assert
    assert result.ocr_text == "Extracted Markdown"
    assert result.arranged_profile.candidate_name == "Jane Doe"
