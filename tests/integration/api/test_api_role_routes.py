import pytest
from unittest.mock import MagicMock, patch

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

# --- Candidate Routes ---

def test_api_candidate_list_jobs(client, candidate_token, mock_get_database):
    mock_get_database.jobs.find.return_value.sort.return_value = [{"id": "1", "title": "Dev"}]
    mock_get_database.candidate_rankings.find.return_value = []
    
    resp = client.get("/api/candidate/jobs", headers={"Authorization": f"Bearer {candidate_token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1

def test_api_candidate_profile(client, candidate_token, mock_get_database):
    mock_get_database.users.find_one.return_value = {"username": "candidate1", "github": "gh"}
    resp = client.get("/api/candidate/profile", headers={"Authorization": f"Bearer {candidate_token}"})
    assert resp.status_code == 200
    assert resp.json()["github"] == "gh"

# --- Recruiter Routes ---

def test_api_recruiter_create_job(client, recruiter_token, mock_get_database, monkeypatch):
    monkeypatch.setattr("services.jobs.generate_embedding", lambda *args: [0.1])
    resp = client.post(
        "/api/recruiter/jobs",
        json={"title": "New Job", "description": "Needs to be at least 300 chars " * 20},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "New Job"

def test_api_recruiter_list_rankings(client, recruiter_token, mock_get_database, monkeypatch):
    mock_list = MagicMock(return_value=[{"id": "r1"}])
    monkeypatch.setattr("api.routes_recruiter.list_candidate_rankings", mock_list)
    
    resp = client.get("/api/recruiter/rankings", headers={"Authorization": f"Bearer {recruiter_token}"})
    assert resp.status_code == 200
    assert resp.json()["count"] == 1

def test_api_recruiter_usage(client, recruiter_token, monkeypatch):
    monkeypatch.setattr("api.routes_recruiter.get_user_usage_summary", lambda u: {"total_tokens": 100})
    resp = client.get("/api/recruiter/usage", headers={"Authorization": f"Bearer {recruiter_token}"})
    assert resp.status_code == 200
    assert resp.json()["total_tokens"] == 100
