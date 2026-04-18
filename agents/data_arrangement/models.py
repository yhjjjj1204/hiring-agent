"""Structured resume profile — same shape as `arranged_profile` in Mongo `resume_ingests`."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

ARRANGEMENT_SCHEMA_VERSION = 1


class EducationEntry(BaseModel):
    institution: str = Field(..., description="School or institution name")
    degree: str | None = Field(default=None, description="Degree level, e.g. BS, MS, PhD")
    field: str | None = Field(default=None, description="Field of study")
    start: str | None = Field(default=None, description="Start date, YYYY or YYYY-MM")
    end: str | None = Field(default=None, description="End date, or present")
    summary: str | None = Field(default=None, description="Short notes for this education block")


class ExperienceEntry(BaseModel):
    company: str = Field(..., description="Company or organization name")
    title: str = Field(..., description="Job title")
    start: str | None = Field(default=None, description="Start date")
    end: str | None = Field(default=None, description="End date or present")
    location: str | None = Field(default=None, description="Work location")
    highlights: list[str] = Field(
        default_factory=list,
        description="Bullet highlights of responsibilities and outcomes (objective, verifiable)",
    )


class SkillEntry(BaseModel):
    name: str = Field(..., description="Skill or tool name")
    level_hint: str | None = Field(
        default=None,
        description="Proficiency hint from context, e.g. multi-year production, coursework only",
    )
    source_evidence: str | None = Field(
        default=None,
        description="Short verbatim or cited phrase supporting the skill judgment",
    )


class ResumeStructuredProfile(BaseModel):
    """Data Arrangement output: maps noisy OCR text to a structured resume."""

    candidate_name: str | None = Field(default=None, description="Candidate name; null if unknown")
    headline: str | None = Field(default=None, description="One-line professional headline")
    summary: str | None = Field(default=None, description="Career summary across the resume")
    education: list[EducationEntry] = Field(default_factory=list, description="Education history, newest first preferred")
    experience: list[ExperienceEntry] = Field(default_factory=list, description="Work history, newest first preferred")
    skills: list[SkillEntry] = Field(default_factory=list, description="Skills list; deduplicate near-duplicates")
    languages: list[str] = Field(
        default_factory=list,
        description="Languages, e.g. English (fluent); empty if none",
    )
    certifications: list[str] = Field(
        default_factory=list,
        description="Certification names",
    )


RESUME_PROFILE_JSON_SCHEMA: dict[str, Any] = ResumeStructuredProfile.model_json_schema()
