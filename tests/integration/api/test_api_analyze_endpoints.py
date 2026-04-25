import pytest
import io
from unittest.mock import MagicMock, patch
from api.auth_models import User

@pytest.fixture
def candidate_token(mock_get_database, monkeypatch):
    mock_user = MagicMock()
    mock_user.username = "candidate1"
    mock_user.role = "candidate"
    monkeypatch.setattr("api.deps.get_user", lambda t: mock_user if t == "cand-token" else None)
    return "cand-token"

@pytest.fixture
def recruiter_token(mock_get_database, monkeypatch):
    mock_user = MagicMock()
    mock_user.username = "recruiter1"
    mock_user.role = "recruiter"
    monkeypatch.setattr("api.deps.get_user", lambda t: mock_user if t == "rec-token" else None)
    return "rec-token"

def test_api_analyze_resume_success(client, candidate_token, mock_get_database, monkeypatch):
    # Mock job
    mock_get_database.jobs.find_one.return_value = {"id": "job1", "description": "desc"}
    # Mock no existing submission
    mock_get_database.candidate_rankings.find_one.return_value = None
    
    monkeypatch.setattr("api.routes_analyze.insert_candidate_ranking", MagicMock())
    
    # Mock file writing
    with patch("pathlib.Path.open", MagicMock()):
        with patch("shutil.copyfileobj", MagicMock()):
            files = {"resume": ("resume.pdf", io.BytesIO(b"content"), "application/pdf")}
            data = {"job_id": "job1"}
            resp = client.post(
                "/api/analyze/resume",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {candidate_token}"}
            )
            
            assert resp.status_code == 200
            assert resp.json()["status"] == "evaluating"

def test_api_re_evaluate_resume(client, recruiter_token, mock_get_database, monkeypatch):
    monkeypatch.setattr("api.routes_analyze.trigger_re_evaluation", AsyncMock(return_value={"status": "evaluating"}))
    
    resp = client.post(
        "/api/analyze/re-evaluate/rank1",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "evaluating"

from unittest.mock import AsyncMock
