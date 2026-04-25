import pytest
from unittest.mock import MagicMock

@pytest.fixture
def recruiter_token(mock_get_database, monkeypatch):
    mock_user = MagicMock()
    mock_user.username = "recruiter1"
    mock_user.role = "recruiter"
    monkeypatch.setattr("api.deps.get_user", lambda t: mock_user if t == "rec-token" else None)
    return "rec-token"

def test_api_create_job(client, recruiter_token, monkeypatch):
    monkeypatch.setattr("services.jobs.generate_embedding", lambda *args: [0.1])
    resp = client.post(
        "/api/jobs",
        json={"title": "New Job", "description": "Desc"},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "New Job"

def test_api_list_jobs(client, mock_get_database):
    mock_get_database.jobs.find.return_value.sort.return_value = [
        {"id": "1", "title": "Job 1", "description": "Desc", "created_at": "2026-04-25T12:00:00Z"}
    ]
    resp = client.get("/api/jobs")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

def test_api_search_jobs(client, mock_get_database, monkeypatch):
    mock_results = [{"id": "1", "title": "Job 1", "description": "Desc", "created_at": "2026-04-25T12:00:00Z"}]
    monkeypatch.setattr("services.jobs.vector_search", MagicMock(return_value=mock_results))
    monkeypatch.setattr("services.jobs.generate_embedding", lambda *args: [0.1])
    
    resp = client.get("/api/jobs/search?q=python")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

def test_api_get_job(client, mock_get_database):
    mock_get_database.jobs.find_one.return_value = {
        "id": "1", "title": "Job 1", "description": "Desc", "created_at": "2026-04-25T12:00:00Z"
    }
    resp = client.get("/api/jobs/1")
    assert resp.status_code == 200
    assert resp.json()["id"] == "1"

def test_api_update_job(client, recruiter_token, mock_get_database, monkeypatch):
    monkeypatch.setattr("services.jobs.generate_embedding", lambda *args: [0.1])
    mock_get_database.jobs.find_one.return_value = {"id": "1", "title": "Old"}
    mock_get_database.jobs.find_one_and_update.return_value = {
        "id": "1", "title": "New", "description": "D", "created_at": "2026-04-25T12:00:00Z"
    }
    
    resp = client.patch(
        "/api/jobs/1",
        json={"title": "New"},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "New"

def test_api_delete_job(client, recruiter_token, mock_get_database):
    mock_get_database.jobs.delete_one.return_value.deleted_count = 1
    resp = client.delete(
        "/api/jobs/1",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
