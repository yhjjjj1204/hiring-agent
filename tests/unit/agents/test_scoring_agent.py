import pytest
from datetime import datetime
from unittest.mock import MagicMock
from agents.scoring.agent import score_match, AnalysisPoints, PointRefutations
from agents.scoring.models import Scorecard, CompetingAnalysis, AnalysisPoint

def test_score_match(mock_chat_openai, monkeypatch):
    # Setup
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    
    # Mock return for Advocate Points
    mock_adv_points = AnalysisPoints(points=[
        {"title": "Skill A", "description": "Good at A"}
    ])
    
    # Mock return for Critic Points
    mock_cri_points = AnalysisPoints(points=[
        {"title": "Weakness B", "description": "Bad at B"}
    ])
    
    # Mock return for Audits
    mock_adv_audit = PointRefutations(refutations=[{"refutation": "Actually not that good"}])
    mock_cri_audit = PointRefutations(refutations=[{"refutation": None}])
    
    # Mock for Judge
    mock_scorecard = Scorecard(
        overall_score=85,
        overall_confidence=0.9,
        summary="Judgment first, then score summary.",
        dimensions=[],
        competing_analysis=CompetingAnalysis(
            advocate_points=[
                AnalysisPoint(title="Skill A", description="Good at A", refutation="Actually not that good")
            ],
            critic_points=[
                AnalysisPoint(title="Weakness B", description="Bad at B")
            ]
        )
    )

    # Use a side effect for invoke on the object returned by with_structured_output
    mock_invoke = MagicMock()
    mock_invoke.invoke.side_effect = [
        mock_adv_points,
        mock_cri_points,
        mock_adv_audit,
        mock_cri_audit,
        mock_scorecard
    ]
    
    monkeypatch.setattr(mock_chat_openai, "with_structured_output", lambda schema: mock_invoke)
    
    # Execute
    result = score_match(
        job_spec={"title": "Python Developer"},
        arranged_resume={"candidate_name": "Alice", "skills": []},
        background_result={"github": {}, "academic": {}}
    )
    
    # Assert
    assert result.overall_score == 85
    assert result.summary == "Judgment first, then score summary."
    assert result.competing_analysis is not None
    assert len(result.competing_analysis.advocate_points) == 1
    assert result.competing_analysis.advocate_points[0].refutation == "Actually not that good"
    
    assert mock_invoke.invoke.call_count == 5

def test_score_match_datetime_serialization(mock_chat_openai, monkeypatch):
    """Verify that datetime objects in input don't crash JSON serialization."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    
    mock_invoke = MagicMock()
    # If points are empty, auditors are NOT called.
    # Total calls: 1. Advocate (empty), 2. Critic (empty), 3. Judge
    mock_scorecard = Scorecard(
        overall_score=80, overall_confidence=1.0, summary="ok", dimensions=[]
    )
    mock_invoke.invoke.side_effect = [
        AnalysisPoints(points=[]),
        AnalysisPoints(points=[]),
        mock_scorecard
    ]
    monkeypatch.setattr(mock_chat_openai, "with_structured_output", lambda schema: mock_invoke)
    
    # Input with datetime
    arranged_resume = {
        "candidate_name": "Alice",
        "last_updated": datetime(2024, 1, 1)
    }
    
    # This should not raise "Object of type datetime is not JSON serializable"
    result = score_match(
        job_spec={},
        arranged_resume=arranged_resume,
        background_result={}
    )
    
    assert result.overall_score == 80
    assert mock_invoke.invoke.call_count == 3
