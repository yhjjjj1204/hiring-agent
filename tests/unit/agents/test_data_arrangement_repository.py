import pytest
from unittest.mock import MagicMock
from agents.data_arrangement.repository import ensure_resume_ingest_indexes, insert_resume_ingest, get_resume_ingest
from agents.data_arrangement.models import ResumeStructuredProfile

def test_ensure_resume_ingest_indexes(mock_get_database):
    ensure_resume_ingest_indexes(mock_get_database)
    assert mock_get_database["resume_ingests"].create_index.called

def test_insert_resume_ingest(mock_get_database):
    profile = ResumeStructuredProfile(candidate_name="Alice")
    insert_resume_ingest(
        ingest_id="1",
        source_filename="a.pdf",
        mime_type="app/pdf",
        ocr_text="text",
        arranged=profile,
        ocr_truncated_for_llm=False,
        db=mock_get_database
    )
    mock_get_database["resume_ingests"].insert_one.assert_called_once()
    doc = mock_get_database["resume_ingests"].insert_one.call_args[0][0]
    assert doc["ingest_id"] == "1"
    assert doc["arranged_profile"]["candidate_name"] == "Alice"

def test_get_resume_ingest(mock_get_database):
    mock_get_database["resume_ingests"].find_one.return_value = {"ingest_id": "1"}
    res = get_resume_ingest("1", mock_get_database)
    assert res["ingest_id"] == "1"
