import pytest
from unittest.mock import MagicMock, patch
from graph.pipeline import (
    node_hr_ingest, node_resume_arrange, node_resume_ocr, 
    node_background, node_fairness_blinding, node_auto_score,
    HiringPipelineState
)
from agents.hr_strategy.models import HRJobSpec, RequiredSkill, CultureFitMetric
from agents.data_arrangement.models import ResumeStructuredProfile
from agents.scoring.models import Scorecard

def test_node_hr_ingest_success(mock_chat_openai, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    mock_moderate = MagicMock()
    mock_moderate.blocked = False
    mock_moderate.as_meta.return_value = {}
    monkeypatch.setattr("graph.pipeline.moderate_text", lambda *args, **kwargs: mock_moderate)
    
    mock_spec = HRJobSpec(
        role_title="Software Engineer",
        summary="Write Python code.",
        required_skills=[RequiredSkill(name="Python", minimum_level="expert")],
        bonus_items=[],
        culture_fit_metrics=[CultureFitMetric(name="Teamwork", description="Work together")]
    )
    mock_chat_openai.mock_structured.invoke.return_value = mock_spec
    
    state: HiringPipelineState = {
        "hr_requirement_text": "We are looking for a senior Python engineer with 5 years experience."
    }
    result = node_hr_ingest(state)
    assert result["pipeline_status"] == "running"
    assert result["job_spec"]["role_title"] == "Software Engineer"

def test_node_resume_ocr_text_input(monkeypatch):
    mock_moderate = MagicMock()
    mock_moderate.blocked = False
    mock_moderate.as_meta.return_value = {"safe": True}
    monkeypatch.setattr("graph.pipeline.moderate_text", lambda *args, **kwargs: mock_moderate)
    
    state: HiringPipelineState = {
        "resume_ocr_text": "This is my resume text."
    }
    res = node_resume_ocr(state)
    assert res["ocr_text"] == "This is my resume text."

def test_node_resume_arrange_success(monkeypatch):
    mock_profile = ResumeStructuredProfile(candidate_name="Bob")
    monkeypatch.setattr(
        "graph.pipeline.arrange_resume_from_ocr_text",
        lambda text: (mock_profile, False, {"sanitized": True})
    )
    state: HiringPipelineState = {"ocr_text": "Some text"}
    res = node_resume_arrange(state)
    assert res["arranged_resume"]["candidate_name"] == "Bob"

def test_node_background(monkeypatch):
    mock_res = MagicMock()
    mock_res.model_dump.return_value = {"github": {"login": "bob"}}
    monkeypatch.setattr("graph.pipeline.run_background_analysis", lambda *args: mock_res)
    
    state: HiringPipelineState = {"arranged_resume": {"candidate_name": "Bob"}}
    res = node_background(state)
    assert res["background_result"]["github"]["login"] == "bob"

def test_node_fairness_blinding():
    state: HiringPipelineState = {
        "arranged_resume": {"candidate_name": "Bob", "skills": []},
        "background_result": {"github": {"login": "bob"}}
    }
    res = node_fairness_blinding(state)
    assert res["arranged_resume_blinded"]["candidate_name"] is None
    assert res["background_result_blinded"]["github"]["login"] is None

def test_node_auto_score_success(monkeypatch):
    mock_scorecard = Scorecard(
        overall_score=80,
        overall_confidence=0.9,
        summary="Good",
        rationale="Match"
    )
    monkeypatch.setattr("graph.pipeline.score_match", lambda *args: mock_scorecard)
    
    mock_moderate = MagicMock()
    mock_moderate.blocked = False
    mock_moderate.as_meta.return_value = {}
    monkeypatch.setattr("graph.pipeline.moderate_text", lambda *args, **kwargs: mock_moderate)
    
    state: HiringPipelineState = {
        "job_spec": {},
        "arranged_resume_blinded": {},
        "background_result_blinded": {}
    }
    res = node_auto_score(state)
    assert res["pipeline_status"] == "completed"
    assert res["scorecard"]["overall_score"] == 80
