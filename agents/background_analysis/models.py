"""Background analysis output: capability graph plus raw metrics."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

BACKGROUND_SCHEMA_VERSION = 1


class GitHubMetrics(BaseModel):
    login: str | None = None
    profile_url: str | None = None
    public_repos: int | None = None
    followers: int | None = None
    following: int | None = None
    account_created_at: str | None = None
    bio: str | None = None
    contributions_last_year: int | None = Field(
        default=None,
        description="Proxy for last-year GitHub activity (GraphQL yearly contributions or REST events)",
    )
    push_events_sampled: int | None = None
    data_source: str = Field(default="none", description="graphql | rest_events | none")


class PaperBrief(BaseModel):
    title: str
    year: int | None = None
    citation_count: int | None = None
    venue: str | None = None
    external_url: str | None = None


class AcademicMetrics(BaseModel):
    """Academic side: aggregated from OpenAlex / Semantic Scholar public APIs (no Scholar page scraping)."""
    display_name: str | None = None
    openalex_author_id: str | None = None
    semantic_scholar_author_id: str | None = None
    works_count: int | None = None
    cited_by_count: int | None = None
    h_index: int | None = None
    top_papers: list[PaperBrief] = Field(default_factory=list)
    identity_match: Literal["name_search", "unverified_claim_url"] = "name_search"
    notes: str | None = Field(
        default=None,
        description="e.g. name-based search may confuse homonyms; Scholar profile URL is not scraped",
    )


class GraphNode(BaseModel):
    id: str
    label: str
    type: Literal["person", "github", "academic", "metric", "reference_link"]
    weight: float | None = Field(default=None, ge=0.0, le=1.0, description="Relative node importance 0–1")
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    weight: float | None = Field(default=None, ge=0.0, le=1.0)


class CapabilityOverviewGraph(BaseModel):
    """Graph payload for force-directed or relationship views."""
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class BackgroundAnalysisResult(BaseModel):
    candidate_name: str | None = None
    github: GitHubMetrics | None = None
    academic: AcademicMetrics | None = None
    graph: CapabilityOverviewGraph
    schema_version: int = BACKGROUND_SCHEMA_VERSION
