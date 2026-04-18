"""Structured job requirements (HR Strategy output) and MongoDB field notes."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

SPEC_SCHEMA_VERSION = 1


class RequiredSkill(BaseModel):
    """A required skill: candidates who clearly miss it should not advance."""

    name: str = Field(..., description="Skill or capability name, e.g. Python, cross-team communication")
    minimum_level: str = Field(
        ...,
        description="Minimum expected proficiency label (e.g. aware / familiar / proficient / expert); keep labels consistent with HR policy",
    )
    evidence: str | None = Field(
        default=None,
        description="Observable signals to validate in resume or interview, e.g. project type, years, certifications",
    )


class BonusItem(BaseModel):
    """Optional plus: increases ranking weight but is not a hard gate."""

    description: str = Field(..., description="What makes this a plus")
    weight: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Relative importance 1–5, default 3",
    )
    signals: list[str] = Field(
        default_factory=list,
        description="Observable signals in resume or interview",
    )


class CultureFitMetric(BaseModel):
    """Culture-fit dimension for interviews and rubrics."""

    name: str = Field(..., description="Metric name, e.g. collaboration style, decision-making")
    description: str = Field(..., description="What this metric means in the team context")
    positive_signals: list[str] = Field(
        default_factory=list,
        description="Typical behaviors when aligned with culture",
    )
    risk_signals: list[str] = Field(
        default_factory=list,
        description="Objective red flags when misaligned (no discriminatory content)",
    )


class HRJobSpec(BaseModel):
    """Structured hiring brief produced by the HR Strategy agent."""

    role_title: str = Field(..., description="Role title")
    team_context: str | None = Field(
        default=None,
        description="Team or business context to help downstream agents",
    )
    location_mode: str | None = Field(
        default=None,
        description="Location or remote policy, e.g. hybrid / remote-first / on-site city",
    )
    seniority: str | None = Field(
        default=None,
        description="Seniority or years expectation, e.g. senior, 5+ years",
    )
    summary: str = Field(
        ...,
        description="One-sentence mission and key outcomes for the role",
    )
    required_skills: list[RequiredSkill] = Field(
        ...,
        min_length=1,
        description="Required skills; at least one entry",
    )
    bonus_items: list[BonusItem] = Field(
        default_factory=list,
        description="Optional bonus items; may be empty",
    )
    culture_fit_metrics: list[CultureFitMetric] = Field(
        ...,
        min_length=1,
        description="Culture-fit metrics; at least one entry",
    )


HR_STRATEGY_JSON_SCHEMA: dict[str, Any] = HRJobSpec.model_json_schema()


# ---------------------------------------------------------------------------
# MongoDB collections (application-level schema, not MongoDB JSON Schema)
# ---------------------------------------------------------------------------
# Collection `hr_strategy_sessions`
# {
#   "session_id": str (UUID),          # unique
#   "status": "collecting" | "completed",
#   "messages": [ { "type", "content", ... } ],  # serialized dialogue
#   "created_at": datetime,
#   "updated_at": datetime
# }
#
# Collection `hr_job_specs`
# {
#   "session_id": str,
#   "schema_version": int,             # matches SPEC_SCHEMA_VERSION
#   "spec": object,                    # same shape as HRJobSpec
#   "json_schema_snapshot": object,  # Pydantic JSON Schema at generation time
#   "created_at": datetime
# }
#
# Indexes are created by agents.hr_strategy.repository.ensure_hr_strategy_indexes.
