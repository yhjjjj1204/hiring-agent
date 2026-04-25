import pytest
from unittest.mock import MagicMock
from services.jobs import create_job, list_jobs, get_job, delete_job
from fastapi import HTTPException

@pytest.fixture
def mock_embeddings(monkeypatch):
    mock_gen = MagicMock(return_value=[0.1, 0.2, 0.3])
    monkeypatch.setattr("services.jobs.generate_embedding", mock_gen)
    return mock_gen

def test_create_job_recruiter(mock_get_database, mock_embeddings, recruiter_user):
    # Execute
    job = create_job(
        title="Software Engineer",
        description="Write code for a living.",
        current_user=recruiter_user
    )
    
    # Assert
    assert job["title"] == "Software Engineer"
    assert "id" in job
    assert mock_get_database.jobs.insert_one.called

def test_create_job_candidate_forbidden(mock_get_database, candidate_user):
    # Execute & Assert
    with pytest.raises(HTTPException) as exc:
        create_job(
            title="Software Engineer",
            description="Short desc",
            current_user=candidate_user
        )
    assert exc.value.status_code == 403

def test_list_jobs(mock_get_database, recruiter_user):
    # Setup
    mock_get_database.jobs.find.return_value.sort.return_value = [
        {"id": "1", "title": "Job 1", "created_at": "now"}
    ]
    mock_get_database.candidate_rankings.find.return_value = []
    
    # Execute
    jobs = list_jobs(current_user=recruiter_user)
    
    # Assert
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Job 1"

def test_get_job_not_found(mock_get_database):
    # Setup
    mock_get_database.jobs.find_one.return_value = None
    
    # Execute & Assert
    with pytest.raises(HTTPException) as exc:
        get_job("nonexistent")
    assert exc.value.status_code == 404
