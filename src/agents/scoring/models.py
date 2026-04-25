from __future__ import annotations

from pydantic import BaseModel, Field


class DimensionScore(BaseModel):
    name: str
    score: float = Field(ge=0, le=100)
    rationale: str = Field(default="", description="Short auditable rationale")


class AnalysisPoint(BaseModel):
    """A single point of analysis with an optional refutation from an auditor."""
    title: str = Field(description="Max 10 words")
    description: str = Field(description="Max 60 words")
    refutation: str | None = Field(default=None, description="Max 60 words, provided by the auditor")


class CompetingAnalysis(BaseModel):
    """Detailed analysis from the multi-agent scoring panel using structured points."""

    advocate_points: list[AnalysisPoint] = Field(default_factory=list)
    critic_points: list[AnalysisPoint] = Field(default_factory=list)


class Scorecard(BaseModel):
    """Aggregate score: job requirements vs resume vs external checks."""

    overall_score: float = Field(ge=0, le=100)
    overall_confidence: float = Field(
        ge=0,
        le=1,
        description="Model confidence in this scorecard; below threshold triggers HITL",
    )
    dimensions: list[DimensionScore] = Field(
        default_factory=list,
        description="e.g. skills fit, experience fit, culture signals, external consistency",
    )
    competing_analysis: CompetingAnalysis | None = Field(
        default=None,
        description="Detailed multi-perspective analysis from competing experts"
    )
    hitl_suggested: bool = Field(
        default=False,
        description="True if ambiguous points should be reviewed by a human",
    )
    hitl_reason: str | None = Field(default=None, description="Why human review is suggested")
    summary: str = Field(default="", description="Short conclusion for HR")
