"""Blind Screening: Redact identifiers like name, gender, and photos before automated scoring."""

from __future__ import annotations

import copy
import re
from typing import Any

_BLIND = "[blinded]"
_PLACEHOLDER = "[identifier removed]"

# Email and Phone (Common CN/US simplified versions)
_RE_EMAIL = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.I,
)
_RE_PHONE = re.compile(
    r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{2,4}[\s-]?\d{2,4}[\s-]?\d{2,6}\b",
)

# Chinese name label line
_RE_NAME_LABEL = re.compile(
    r"(姓名|名字|本名)[:：\s]*([\u4e00-\u9fa5·]{2,16})",
    re.I,
)
# English Mr./Ms. + Name
_RE_EN_NAME = re.compile(
    r"\b(Mr|Ms|Mrs|Miss)\.?\s+[A-Z][a-zA-Z'-]+\b",
    re.I,
)

# Gender related (labels + common tokens)
_RE_GENDER_LABEL = re.compile(
    r"(性别|sex|gender)\s*[:：]?\s*(男|女|男性|女性|其他|保密|不详|unknown|male|female|other)\b",
    re.I,
)
_RE_GENDER_TOKEN = re.compile(r"\b(male|female)\b", re.I)

# Markdown / HTML images
_RE_MD_IMG = re.compile(r"!\[[^\]]*\]\([^)]+\)")
_RE_HTML_IMG = re.compile(r"<img\b[^>]*>", re.I)


def redact_identifiers_in_text(text: str | None) -> str | None:
    """Redact identifiers in free text (used for headline/summary, etc.)."""
    if not text:
        return text
    s = text
    s = _RE_EMAIL.sub(_PLACEHOLDER, s)
    s = _RE_PHONE.sub(_PLACEHOLDER, s)
    s = _RE_NAME_LABEL.sub(lambda m: f"{m.group(1)}: {_BLIND}", s)
    s = _RE_EN_NAME.sub(_PLACEHOLDER, s)
    s = _RE_GENDER_LABEL.sub(lambda m: f"{m.group(1)}: {_BLIND}", s)
    s = _RE_GENDER_TOKEN.sub(_BLIND, s)
    s = _RE_MD_IMG.sub(_PLACEHOLDER, s)
    s = _RE_HTML_IMG.sub(_PLACEHOLDER, s)
    return s


def blind_screen_resume_profile(data: dict[str, Any]) -> dict[str, Any]:
    """
    Deep copy resume JSON and remove/redact candidate identification fields.
    Preserves skills and experience structure for fair scoring.
    """
    out: dict[str, Any] = copy.deepcopy(data)
    out["candidate_name"] = None
    if "headline" in out:
        out["headline"] = redact_identifiers_in_text(out.get("headline"))
    if "summary" in out:
        out["summary"] = redact_identifiers_in_text(out.get("summary"))

    for edu in out.get("education") or []:
        if isinstance(edu, dict) and edu.get("summary"):
            edu["summary"] = redact_identifiers_in_text(edu.get("summary"))

    for exp in out.get("experience") or []:
        if not isinstance(exp, dict):
            continue
        for k in ("highlights",):
            hs = exp.get(k)
            if isinstance(hs, list):
                exp[k] = [
                    t
                    for h in hs
                    if isinstance(h, str)
                    for t in [redact_identifiers_in_text(h) or ""]
                    if t
                ]

    for sk in out.get("skills") or []:
        if isinstance(sk, dict) and sk.get("source_evidence"):
            sk["source_evidence"] = redact_identifiers_in_text(sk.get("source_evidence"))

    out["_blind_screening"] = {"version": 1, "applied": True}
    return out


def blind_screen_background_for_scoring(bg: dict[str, Any]) -> dict[str, Any]:
    """
    Construct a blinded background summary for scoring.
    Removes strong identifiers (GitHub login, academic display name) while
    preserving aggregate metrics (contribution proxy, citations) for consistency checks.
    """
    out: dict[str, Any] = copy.deepcopy(bg)
    gh = out.get("github")
    if isinstance(gh, dict):
        gh["login"] = None
        gh["profile_url"] = None
        if gh.get("bio"):
            gh["bio"] = redact_identifiers_in_text(gh.get("bio"))
    ac = out.get("academic")
    if isinstance(ac, dict):
        ac["display_name"] = None
        ac["openalex_author_id"] = None
        ac["semantic_scholar_author_id"] = None
        if ac.get("notes"):
            ac["notes"] = redact_identifiers_in_text(ac.get("notes"))
        for p in ac.get("top_papers") or []:
            if isinstance(p, dict) and p.get("external_url"):
                p["external_url"] = None

    graph = out.get("graph")
    if isinstance(graph, dict):
        for node in graph.get("nodes") or []:
            if not isinstance(node, dict):
                continue
            md = node.get("metadata")
            if isinstance(md, dict):
                for k in ("login", "profile_url", "display_name", "openalex_author_id", "semantic_scholar_author_id"):
                    if k in md:
                        md[k] = None
                if isinstance(md.get("bio"), str):
                    md["bio"] = redact_identifiers_in_text(md.get("bio"))

    out["_blind_screening"] = {"version": 1, "applied": True}
    return out
