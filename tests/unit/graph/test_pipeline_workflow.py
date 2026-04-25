import pytest
from unittest.mock import MagicMock, patch
from graph.pipeline import node_hr_ingest, node_resume_arrange, node_resume_ocr, HiringPipelineState
from agents.hr_strategy.models import HRJobSpec, RequiredSkill, CultureFitMetric
from agents.data_arrangement.models import ResumeStructuredProfile

def test_node_hr_ingest_success(mock_chat_openai, monkeypatch):
    # Setup
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    
    # Mock safety check
    mock_moderate = MagicMock()
    mock_moderate.blocked = False
    mock_moderate.as_meta.return_value = {}
    monkeypatch.setattr("graph.pipeline.moderate_text", lambda *args, **kwargs: mock_moderate)
    
    # Mock LLM extraction
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
    
    # Execute
    result = node_hr_ingest(state)
    
    # Assert
    assert result["pipeline_status"] == "running"
    assert result["job_spec"]["role_title"] == "Software Engineer"
    assert "hr_requirement_text" in result

def test_node_hr_ingest_too_short(monkeypatch):
    # Mock interrupt to avoid "Called get_config outside of a runnable context"
    mock_interrupt = MagicMock(side_effect=RuntimeError("MockInterrupt"))
    monkeypatch.setattr("graph.pipeline.interrupt", mock_interrupt)
    
    state: HiringPipelineState = {
        "hr_requirement_text": "Too short"
    }
    
    with pytest.raises(RuntimeError) as excinfo:
        node_hr_ingest(state)
    
    assert "MockInterrupt" in str(excinfo.value)

def test_node_resume_ocr_text_input(monkeypatch):
    # Mock moderate_text
    mock_moderate = MagicMock()
    mock_moderate.blocked = False
    mock_moderate.as_meta.return_value = {"safe": True}
    monkeypatch.setattr("graph.pipeline.moderate_text", lambda *args, **kwargs: mock_moderate)
    
    state: HiringPipelineState = {
        "resume_ocr_text": "This is my resume text."
    }
    
    res = node_resume_ocr(state)
    assert res["ocr_text"] == "This is my resume text."
    assert res["safety_meta"]["resume_ocr_input"]["safe"] is True

def test_node_resume_arrange_success(monkeypatch):
    # Mock arrange_resume_from_ocr_text
    mock_profile = ResumeStructuredProfile(candidate_name="Bob")
    monkeypatch.setattr(
        "graph.pipeline.arrange_resume_from_ocr_text",
        lambda text: (mock_profile, False, {"sanitized": True})
    )
    
    state: HiringPipelineState = {
        "ocr_text": "Some OCR text about Bob"
    }
    
    res = node_resume_arrange(state)
    assert res["arranged_resume"]["candidate_name"] == "Bob"
    assert res["pipeline_status"] == "running"

def test_node_resume_arrange_empty_ocr():
    state: HiringPipelineState = {
        "ocr_text": ""
    }
    res = node_resume_arrange(state)
    assert res["pipeline_status"] == "failed"
    assert res["last_error"] == "empty_ocr"
