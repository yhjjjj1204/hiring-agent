"""Academic public data via OpenAlex + Semantic Scholar HTTP APIs (no Scholar page scraping)."""

from __future__ import annotations

import math
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx

from hiring_agent import config as app_config
from hiring_agent.agents.background_analysis.models import AcademicMetrics, PaperBrief

_OPENALEX = "https://api.openalex.org"
_S2 = "https://api.semanticscholar.org/graph/v1"


def _ua() -> str:
    c = (app_config.HTTP_USER_AGENT_CONTACT or "").strip()
    if c:
        return f"HiringAgent/1.0 ({c})"
    return "HiringAgent/1.0 (academic-api; +https://openalex.org)"


def parse_google_scholar_user_id(url: str | None) -> str | None:
    if not url:
        return None
    if "scholar.google" not in url.lower():
        return None
    q = parse_qs(urlparse(url.strip()).query)
    u = (q.get("user") or [None])[0]
    return u


def _top_works_openalex(client: httpx.Client, author_id_url: str, limit: int = 5) -> list[PaperBrief]:
    """author_id_url looks like https://openalex.org/A1234567890"""
    filt = f"authorships.author.id:{author_id_url}"
    r = client.get(
        f"{_OPENALEX}/works",
        params={"filter": filt, "per_page": limit, "sort": "cited_by_count:desc"},
        headers={"User-Agent": _ua()},
    )
    if r.status_code != 200:
        return []
    out: list[PaperBrief] = []
    for w in (r.json().get("results") or [])[:limit]:
        title = (w.get("title") or w.get("display_name") or "").strip() or "(untitled)"
        year = w.get("publication_year")
        cc = w.get("cited_by_count")
        venue = None
        host = w.get("host_venue") or {}
        if isinstance(host, dict):
            venue = host.get("display_name")
        ext = w.get("id")
        out.append(
            PaperBrief(
                title=title,
                year=int(year) if isinstance(year, int) else None,
                citation_count=int(cc) if isinstance(cc, int) else None,
                venue=venue,
                external_url=ext if isinstance(ext, str) else None,
            ),
        )
    return out


def _openalex_author_by_name(client: httpx.Client, name: str) -> dict[str, Any] | None:
    r = client.get(
        f"{_OPENALEX}/authors",
        params={"search": name, "per_page": 10, "sort": "cited_by_count:desc"},
        headers={"User-Agent": _ua()},
    )
    r.raise_for_status()
    results = r.json().get("results") or []
    if not results:
        return None
    best = max(results, key=lambda a: int(a.get("cited_by_count") or 0))
    return best


def _s2_author_by_name(client: httpx.Client, name: str) -> dict[str, Any] | None:
    r = client.get(
        f"{_S2}/author/search",
        params={"query": name, "limit": 5, "fields": "authorId,name,hIndex,citationCount,paperCount"},
        headers={"User-Agent": _ua()},
    )
    if r.status_code != 200:
        return None
    data = r.json().get("data") or []
    if not data:
        return None
    return max(data, key=lambda a: int(a.get("citationCount") or 0))


def _s2_papers(client: httpx.Client, author_id: str, limit: int = 5) -> list[PaperBrief]:
    r = client.get(
        f"{_S2}/author/{author_id}",
        params={
            "fields": "papers.title,papers.year,papers.citationCount,papers.publicationVenue,papers.url",
        },
        headers={"User-Agent": _ua()},
    )
    if r.status_code != 200:
        return []
    papers = (r.json().get("papers") or [])[:limit]
    out: list[PaperBrief] = []
    for p in papers:
        venue = p.get("publicationVenue")
        if isinstance(venue, dict):
            venue = venue.get("name")
        out.append(
            PaperBrief(
                title=(p.get("title") or "").strip() or "(untitled)",
                year=int(p["year"]) if p.get("year") is not None else None,
                citation_count=int(p["citationCount"]) if p.get("citationCount") is not None else None,
                venue=venue if isinstance(venue, str) else None,
                external_url=p.get("url"),
            ),
        )
    return out


def fetch_academic_metrics(
    candidate_name: str | None,
    google_scholar_url: str | None = None,
    timeout: float = 30.0,
) -> AcademicMetrics | None:
    query_name = (candidate_name or "").strip()
    scholar_uid = parse_google_scholar_user_id(google_scholar_url)
    if not query_name and not scholar_uid:
        return None
    if not query_name and scholar_uid:
        return AcademicMetrics(
            display_name=None,
            openalex_author_id=None,
            semantic_scholar_author_id=None,
            works_count=None,
            cited_by_count=None,
            h_index=None,
            top_papers=[],
            identity_match="unverified_claim_url",
            notes=(
                "With only a Google Scholar URL and no candidate name, OpenAlex / Semantic Scholar "
                "cannot reliably resolve an author. Add a name and retry; this result keeps only the claimed link node."
            ),
        )

    with httpx.Client(timeout=timeout) as client:
        oa_author: dict[str, Any] | None = None
        s2_author: dict[str, Any] | None = None
        try:
            oa_author = _openalex_author_by_name(client, query_name)
        except (httpx.HTTPError, ValueError, KeyError):
            oa_author = None
        try:
            s2_author = _s2_author_by_name(client, query_name)
        except (httpx.HTTPError, ValueError, KeyError):
            s2_author = None

        oa_id = oa_author.get("id") if oa_author else None
        oa_cited = int(oa_author.get("cited_by_count") or 0) if oa_author else 0
        oa_works = int(oa_author.get("works_count") or 0) if oa_author else 0
        oa_name = (oa_author or {}).get("display_name")

        s2_id = s2_author.get("authorId") if s2_author else None
        s2_cited = int(s2_author.get("citationCount") or 0) if s2_author else 0
        s2_h = s2_author.get("hIndex") if s2_author else None
        s2_papers_n = int(s2_author.get("paperCount") or 0) if s2_author else 0

        cited_by = max(oa_cited, s2_cited)
        works = max(oa_works, s2_papers_n)
        h_index: int | None = None
        if isinstance(s2_h, int):
            h_index = s2_h
        elif oa_author and (oa_author or {}).get("summary_stats"):
            ss = (oa_author or {}).get("summary_stats") or {}
            hi = ss.get("h_index")
            if isinstance(hi, int):
                h_index = hi

        papers: list[PaperBrief] = []
        if oa_id:
            papers = _top_works_openalex(client, oa_id, limit=5)
        if len(papers) < 3 and s2_id:
            papers = _merge_paper_lists(papers, _s2_papers(client, s2_id, limit=5))

        identity = "name_search"
        notes_parts = [
            "Academic metrics come from OpenAlex / Semantic Scholar public APIs; Google Scholar pages are not scraped.",
            "Name-based search may match a homonym; verify against the resume manually.",
        ]
        if google_scholar_url and scholar_uid:
            identity = "unverified_claim_url"
            notes_parts.append(
                f"The provided Scholar profile is a reference link only (user={scholar_uid}); "
                "it is not automatically bound to an OpenAlex authoritative ID."
            )

        return AcademicMetrics(
            display_name=oa_name or (s2_author or {}).get("name") or query_name,
            openalex_author_id=oa_id,
            semantic_scholar_author_id=s2_id,
            works_count=works or None,
            cited_by_count=cited_by or None,
            h_index=h_index,
            top_papers=papers[:8],
            identity_match=identity,
            notes=" ".join(notes_parts),
        )


def _merge_paper_lists(a: list[PaperBrief], b: list[PaperBrief]) -> list[PaperBrief]:
    seen: set[str] = set()
    out: list[PaperBrief] = []
    for p in a + b:
        key = re.sub(r"\s+", " ", p.title.lower())[:200]
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    out.sort(key=lambda x: int(x.citation_count or 0), reverse=True)
    return out[:8]


def citation_impact_index(cited_by: int | None) -> float:
    if not cited_by:
        return 0.0
    return min(1.0, math.log1p(cited_by) / math.log1p(50_000))


def code_activity_index(contributions: int | None) -> float:
    if not contributions:
        return 0.0
    return min(1.0, math.log1p(contributions) / math.log1p(5_000))
