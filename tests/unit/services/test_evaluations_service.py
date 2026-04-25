import pytest
from unittest.mock import MagicMock, patch, mock_open
from services.evaluations import submit_resume_for_analysis
from fastapi import HTTPException, UploadFile
import io

@pytest.mark.asyncio
async def test_submit_resume_for_analysis_success(mock_get_database, candidate_user, monkeypatch):
    # Setup
    mock_get_database.jobs.find_one.return_value = {"id": "job1", "description": "desc"}
    mock_get_database.candidate_rankings.find_one.return_value = None
    
    mock_bt = MagicMock()
    
    # Mock resume file
    mock_file_content = b"pdf content"
    mock_resume = MagicMock(spec=UploadFile)
    mock_resume.filename = "resume.pdf"
    mock_resume.file = io.BytesIO(mock_file_content)
    
    # Mock insert_candidate_ranking
    mock_insert_repo = MagicMock()
    monkeypatch.setattr("services.evaluations.insert_candidate_ranking", mock_insert_repo)
    
    # Mock _background_evaluate_resume
    mock_bg_eval = MagicMock()
    monkeypatch.setattr("api.routes_analyze._background_evaluate_resume", mock_bg_eval)
    
    # Mock file writing
    with patch("pathlib.Path.open", mock_open()) as mocked_file:
        res = await submit_resume_for_analysis(
            background_tasks=mock_bt,
            resume=mock_resume,
            job_id="job1",
            current_user=candidate_user
        )
        
        assert res["status"] == "evaluating"
        assert "ranking_id" in res
        assert mock_insert_repo.called
        assert mock_bt.add_task.called

@pytest.mark.asyncio
async def test_submit_resume_for_analysis_job_not_found(mock_get_database, candidate_user):
    mock_get_database.jobs.find_one.return_value = None
    mock_bt = MagicMock()
    mock_resume = MagicMock(spec=UploadFile)
    
    with pytest.raises(HTTPException) as exc:
        await submit_resume_for_analysis(mock_bt, mock_resume, "nonexistent", candidate_user)
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_submit_resume_for_analysis_unsupported_suffix(mock_get_database, candidate_user):
    mock_get_database.jobs.find_one.return_value = {"id": "job1"}
    mock_bt = MagicMock()
    mock_resume = MagicMock(spec=UploadFile)
    mock_resume.filename = "resume.exe"
    
    with pytest.raises(HTTPException) as exc:
        await submit_resume_for_analysis(mock_bt, mock_resume, "job1", candidate_user)
    assert exc.value.status_code == 400
