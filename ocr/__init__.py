from hiring_agent.agents.ocr_agent import (
    extract_resume_text_from_path,
    is_allowed_upload_suffix,
    is_supported_suffix,
)

extract_text_from_path = extract_resume_text_from_path

__all__ = ["extract_text_from_path", "extract_resume_text_from_path", "is_allowed_upload_suffix", "is_supported_suffix"]
