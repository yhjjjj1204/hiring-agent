"""GitHub 公开 API：用户画像与贡献活动代理（非网页爬虫）。"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from hiring_agent import config
from hiring_agent.agents.background_analysis.models import GitHubMetrics

_GITHUB_API = "https://api.github.com"
_GITHUB_GRAPHQL = "https://api.github.com/graphql"

_UA = "HiringAgent/1.0 (+https://github.com)"


def parse_github_login(raw: str | None) -> str | None:
    if not raw:
        return None
    s = raw.strip().lstrip("@")
    if not s:
        return None
    if "github.com" in s.lower():
        m = re.search(r"github\.com/([^/?#]+)", s, re.I)
        if m:
            seg = m.group(1)
            if seg.lower() not in ("orgs", "settings", "topics", "explore", "marketplace", "sponsors"):
                return seg.split("/")[0]
        return None
    if re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}", s):
        return s
    return None


def _github_headers() -> dict[str, str]:
    h = {"Accept": "application/vnd.github+json", "User-Agent": _UA, "X-GitHub-Api-Version": "2022-11-28"}
    if config.GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
    return h


def fetch_github_metrics(login: str, timeout: float = 25.0) -> GitHubMetrics | None:
    login = login.strip()
    if not login:
        return None

    with httpx.Client(timeout=timeout, headers=_github_headers()) as client:
        r = client.get(f"{_GITHUB_API}/users/{login}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        u: dict[str, Any] = r.json()

        contributions: int | None = None
        push_sampled: int | None = None
        source = "none"

        if config.GITHUB_TOKEN:
            gql = _graphql_contributions(client, login)
            if gql is not None:
                contributions = gql
                source = "graphql"

        if contributions is None:
            push_sampled = _count_recent_push_events(client, login)
            if push_sampled is not None:
                contributions = push_sampled
                source = "rest_events"
            else:
                source = "none"

        return GitHubMetrics(
            login=u.get("login"),
            profile_url=u.get("html_url"),
            public_repos=u.get("public_repos"),
            followers=u.get("followers"),
            following=u.get("following"),
            account_created_at=u.get("created_at"),
            bio=u.get("bio"),
            contributions_last_year=contributions,
            push_events_sampled=push_sampled if source == "rest_events" else None,
            data_source=source,
        )


def _graphql_contributions(client: httpx.Client, login: str) -> int | None:
    to_dt = datetime.now(timezone.utc)
    from_dt = to_dt - timedelta(days=365)
    q = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar { totalContributions }
        }
      }
    }
    """
    payload = {
        "query": q,
        "variables": {
            "login": login,
            "from": from_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": to_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }
    r = client.post(_GITHUB_GRAPHQL, json=payload)
    if r.status_code in (401, 403, 404):
        return None
    if r.status_code != 200:
        return None
    data = r.json()
    if data.get("errors"):
        return None
    user = (data.get("data") or {}).get("user") or {}
    coll = user.get("contributionsCollection") or {}
    cal = coll.get("contributionCalendar") or {}
    tc = cal.get("totalContributions")
    return int(tc) if isinstance(tc, int) else None


def _count_recent_push_events(client: httpx.Client, login: str, max_pages: int = 3) -> int | None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=365)
    total = 0
    for page in range(1, max_pages + 1):
        r = client.get(
            f"{_GITHUB_API}/users/{login}/events/public",
            params={"per_page": 100, "page": page},
        )
        if r.status_code != 200:
            return total if total else None
        events = r.json()
        if not isinstance(events, list) or not events:
            break
        for ev in events:
            if ev.get("type") != "PushEvent":
                continue
            created = ev.get("created_at")
            if not created:
                continue
            try:
                ts = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except ValueError:
                continue
            if ts >= cutoff:
                total += 1
        if len(events) < 100:
            break
    return total
