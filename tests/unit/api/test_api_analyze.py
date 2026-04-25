import pytest
import json
from unittest.mock import MagicMock, patch
from api.routes_analyze import _resolve_job_spec, _background_evaluate_resume
from agents.hr_strategy.models import HRJobSpec, RequiredSkill, CultureFitMetric
from fastapi import HTTPException

def test_resolve_job_spec_json():
    spec = HRJobSpec(
        role_title="Dev",
        summary="code",
        required_skills=[RequiredSkill(name="Python", minimum_level="mid")],
        culture_fit_metrics=[CultureFitMetric(name="Team", description="good")]
    )
    res = _resolve_job_spec(None, spec.model_dump_json())
    assert res["role_title"] == "Dev"

def test_resolve_job_spec_text(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    mock_extract = MagicMock(return_value={"role_title": "Extracted"})
    monkeypatch.setattr("api.routes_analyze.extract_hr_job_spec_from_text", mock_extract)
    
    res = _resolve_job_spec("We need a dev", None)
    assert res["role_title"] == "Extracted"
    mock_extract.assert_called_once_with("We need a dev")

@pytest.mark.asyncio
async def test_background_evaluate_resume_success(mock_get_database, mock_chat_openai, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    
    # Mock _resolve_job_spec
    monkeypatch.setattr("api.routes_analyze._resolve_job_spec", lambda t, j: {"role_title": "Dev"})
    
    # Mock extract_and_arrange_resume_from_path
    mock_extracted = MagicMock()
    mock_extracted.ocr_text = "Resume text"
    mock_extracted.arranged_profile.model_dump.return_value = {"name": "Bob"}
    monkeypatch.setattr("api.routes_analyze.extract_and_arrange_resume_from_path", lambda p: mock_extracted)
    
    # Mock safety check
    mock_moderate = MagicMock()
    mock_moderate.blocked = False
    monkeypatch.setattr("safety.guardrails.moderate_text", lambda *args, **kwargs: mock_moderate)
    
    # Mock background analysis
    mock_bg = MagicMock()
    mock_bg.model_dump.return_value = {}
    monkeypatch.setattr("api.routes_analyze.run_background_analysis", mock_bg)
    
    # Mock scoring
    mock_scorecard = MagicMock()
    mock_scorecard.model_dump.return_value = {
        "overall_score": 90,
        "summary": "Good",
        "dimensions": [{"name": "Skill", "score": 90, "rationale": "ok"}]
    }
    monkeypatch.setattr("api.routes_analyze.score_match", MagicMock(return_value=mock_scorecard))
    
    # Mock repository
    mock_update = MagicMock()
    monkeypatch.setattr("api.routes_analyze.update_candidate_ranking_result", mock_update)
    
    # Execute
    from pathlib import Path
    await _background_evaluate_resume(
        ranking_id="rank1",
        resume_path=Path("dummy.pdf"),
        hr_requirement_text="desc",
        job_spec_json=None,
        candidate_github=None,
        google_scholar_url=None,
        candidate_name_override=None,
        username="tester"
    )
    
    assert mock_update.called
    # Ensure dimensions were passed correctly
    call_args = mock_update.call_args[1]
    assert call_args["overall_score"] == 90
    assert len(call_args["dimensions"]) == 1
    assert call_args["dimensions"][0]["name"] == "Skill"
