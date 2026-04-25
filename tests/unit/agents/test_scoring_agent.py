import pytest
from agents.scoring.agent import score_match
from agents.scoring.models import Scorecard

def test_score_match(mock_chat_openai, monkeypatch):
    # Setup
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    
    mock_scorecard = Scorecard(
        overall_score=85,
        overall_confidence=0.9,
        summary="Strong candidate",
        rationale="Strong match",
        skill_scores={"Python": 90}
    )
    mock_chat_openai.mock_structured.invoke.return_value = mock_scorecard
    
    # Execute
    result = score_match(
        job_spec={"title": "Python Developer"},
        arranged_resume={"candidate_name": "Alice", "skills": []},
        background_result={"github": {}, "academic": {}}
    )
    
    # Assert
    assert result.overall_score == 85
    assert result.summary == "Strong candidate"
    assert mock_chat_openai.mock_structured.invoke.called
