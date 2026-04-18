from __future__ import annotations

from pydantic import BaseModel, Field


class DimensionScore(BaseModel):
    name: str
    score: float = Field(ge=0, le=100)
    rationale: str = Field(default="", description="Short auditable rationale")


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
    hitl_suggested: bool = Field(
        default=False,
        description="True if ambiguous points should be reviewed by a human",
    )
    hitl_reason: str | None = Field(default=None, description="Why human review is suggested")
    summary: str = Field(default="", description="Short conclusion for HR")
