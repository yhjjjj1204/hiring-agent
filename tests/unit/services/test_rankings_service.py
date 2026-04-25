import pytest
from unittest.mock import MagicMock, patch
from services.rankings import list_candidate_rankings, get_my_submission, trigger_re_evaluation
from fastapi import HTTPException

@pytest.fixture
def mock_rankings_repo(monkeypatch):
    mock_list = MagicMock()
    monkeypatch.setattr("services.rankings.list_rankings_repo", mock_list)
    return mock_list

def test_list_candidate_rankings_recruiter(mock_rankings_repo, recruiter_user):
    list_candidate_rankings(recruiter_user, job_id="job1")
    # For recruiter, candidate_ref should be None
    mock_rankings_repo.assert_called_with(limit=50, sort_by="overall_score", job_id="job1", candidate_ref=None)

def test_list_candidate_rankings_candidate(mock_rankings_repo, candidate_user):
    list_candidate_rankings(candidate_user, job_id="job1")
    # For candidate, candidate_ref should be their username
    mock_rankings_repo.assert_called_with(limit=50, sort_by="overall_score", job_id="job1", candidate_ref="candidate1")

def test_get_my_submission_success(mock_get_database, candidate_user):
    mock_get_database.candidate_rankings.find_one.return_value = {"id": "rank1", "candidate_ref": "candidate1"}
    res = get_my_submission("job1", candidate_user)
    assert res["candidate_ref"] == "candidate1"

def test_get_my_submission_forbidden(recruiter_user):
    with pytest.raises(HTTPException) as exc:
        get_my_submission("job1", recruiter_user)
    assert exc.value.status_code == 403

@pytest.mark.asyncio
async def test_trigger_re_evaluation_recruiter(mock_get_database, recruiter_user, monkeypatch):
    mock_get_database.candidate_rankings.find_one.return_value = {"ranking_id": "rank1", "job_id": "job1"}
    mock_get_database.jobs.find_one.return_value = {"id": "job1", "description": "desc"}
    
    # Mock glob to find a file
    with patch("pathlib.Path.glob") as mock_glob:
        mock_glob.return_value = [MagicMock()]
        
        # Mock background tasks
        mock_bt = MagicMock()
        
        # Mock _background_evaluate_resume import
        monkeypatch.setattr("api.routes_analyze._background_evaluate_resume", MagicMock())
        
        from services.rankings import trigger_re_evaluation
        res = await trigger_re_evaluation("rank1", recruiter_user, mock_bt)
        
        assert res["status"] == "evaluating"
        assert mock_bt.add_task.called
