import pytest
from unittest.mock import MagicMock
from dashboard.ranking_service import record_pipeline_ranking

def test_record_pipeline_ranking_success(monkeypatch):
    mock_insert = MagicMock()
    monkeypatch.setattr("dashboard.ranking_service.insert_candidate_ranking", mock_insert)
    
    state = {
        "scorecard": {
            "overall_score": 85,
            "summary": "Good",
            "dimensions": [{"name": "Skill", "score": 90}]
        },
        "candidate_ref": "alice",
        "job_id": "job1"
    }
    
    rid = record_pipeline_ranking("thread1", state)
    assert rid is not None
    assert mock_insert.called
    args = mock_insert.call_args[1]
    assert args["candidate_ref"] == "alice"
    assert args["overall_score"] == 85.0
    assert args["dimensions"][0]["name"] == "Skill"

def test_record_pipeline_ranking_no_scorecard():
    rid = record_pipeline_ranking("thread1", {})
    assert rid is None
