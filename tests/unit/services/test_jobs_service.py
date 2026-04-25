import pytest
from unittest.mock import MagicMock, patch
from services.jobs import create_job, list_jobs, get_job, delete_job, update_job, search_jobs, _generate_job_summary
from fastapi import HTTPException, BackgroundTasks

@pytest.fixture
def mock_embeddings(monkeypatch):
    mock_gen = MagicMock(return_value=[0.1, 0.2, 0.3])
    # Patch generate_embedding in both db.mongo and services.jobs if needed
    monkeypatch.setattr("services.jobs.generate_embedding", mock_gen)
    monkeypatch.setattr("db.mongo.generate_embedding", mock_gen)
    return mock_gen

def test_create_job_recruiter(mock_get_database, mock_embeddings, recruiter_user):
    job = create_job(
        title="Software Engineer",
        description="Write code for a living.",
        current_user=recruiter_user
    )
    assert job["title"] == "Software Engineer"
    assert "id" in job
    assert mock_get_database.jobs.insert_one.called

def test_create_job_candidate_forbidden(mock_get_database, candidate_user):
    with pytest.raises(HTTPException) as exc:
        create_job(
            title="Software Engineer",
            description="Short desc",
            current_user=candidate_user
        )
    assert exc.value.status_code == 403

def test_list_jobs(mock_get_database, recruiter_user):
    mock_get_database.jobs.find.return_value.sort.return_value = [
        {"id": "1", "title": "Job 1", "created_at": "now"}
    ]
    mock_get_database.candidate_rankings.find.return_value = []
    jobs = list_jobs(current_user=recruiter_user)
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Job 1"

def test_get_job_not_found(mock_get_database):
    mock_get_database.jobs.find_one.return_value = None
    with pytest.raises(HTTPException) as exc:
        get_job("nonexistent")
    assert exc.value.status_code == 404

def test_update_job_success(mock_get_database, mock_embeddings, recruiter_user):
    mock_get_database.jobs.find_one.return_value = {"id": "1", "title": "Old", "description": "Old desc"}
    mock_get_database.jobs.find_one_and_update.return_value = {"id": "1", "title": "New"}
    
    res = update_job("1", title="New", description=None, current_user=recruiter_user)
    assert res["title"] == "New"
    assert mock_get_database.jobs.find_one_and_update.called

def test_delete_job_success(mock_get_database, recruiter_user):
    mock_get_database.jobs.delete_one.return_value.deleted_count = 1
    res = delete_job("1", recruiter_user)
    assert res is True

def test_delete_job_not_found(mock_get_database, recruiter_user):
    mock_get_database.jobs.delete_one.return_value.deleted_count = 0
    with pytest.raises(HTTPException) as exc:
        delete_job("1", recruiter_user)
    assert exc.value.status_code == 404

def test_search_jobs(mock_get_database, mock_embeddings, candidate_user, monkeypatch):
    mock_results = [{"id": "1", "title": "Job 1"}]
    monkeypatch.setattr("services.jobs.vector_search", MagicMock(return_value=mock_results))
    mock_get_database.candidate_rankings.find.return_value = []
    
    res = search_jobs("python", current_user=candidate_user)
    assert len(res) == 1
    assert res[0]["title"] == "Job 1"

def test_generate_job_summary_short(monkeypatch):
    # Should return empty for short descriptions
    res = _generate_job_summary("Title", "Short")
    assert res == ""

def test_generate_job_summary_long(mock_chat_openai, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    mock_chat_openai.invoke.return_value = MagicMock(content="Summary")
    
    res = _generate_job_summary("Title", "Long description " * 100)
    assert res == "Summary"
