"""编排 GitHub + 学术 API，生成能力概览图谱。"""

from __future__ import annotations

import logging

from hiring_agent.agents.background_analysis.academic_client import (
    citation_impact_index,
    code_activity_index,
    fetch_academic_metrics,
)
from hiring_agent.agents.background_analysis.github_client import fetch_github_metrics, parse_github_login
from hiring_agent.agents.background_analysis.models import (
    AcademicMetrics,
    BackgroundAnalysisResult,
    CapabilityOverviewGraph,
    GitHubMetrics,
    GraphEdge,
    GraphNode,
)

logger = logging.getLogger(__name__)


def run_background_analysis(
    candidate_name: str | None,
    github_url_or_username: str | None = None,
    google_scholar_url: str | None = None,
) -> BackgroundAnalysisResult:
    """
    输入：姓名（用于学术检索）、GitHub 用户名或仓库主页链接、可选 Google Scholar 个人主页链接。
    输出：GitHub 活动指标、基于 OpenAlex/S2 的引用与论文摘要、力导向图可用的 nodes/edges。
    """
    gh_login = parse_github_login(github_url_or_username)
    gh: GitHubMetrics | None = None
    if gh_login:
        try:
            gh = fetch_github_metrics(gh_login)
        except Exception as e:
            logger.warning("GitHub fetch failed login=%s: %s", gh_login, e)

    ac: AcademicMetrics | None = None
    try:
        ac = fetch_academic_metrics(candidate_name, google_scholar_url)
    except Exception as e:
        logger.warning("Academic API fetch failed: %s", e)

    label_name = (candidate_name or "").strip() or "Candidate"
    nodes: list[GraphNode] = [
        GraphNode(
            id="n_candidate",
            label=label_name,
            type="person",
            weight=1.0,
            metadata={"role": "candidate"},
        ),
    ]
    edges: list[GraphEdge] = []

    if gh and gh.login:
        w_code = code_activity_index(gh.contributions_last_year)
        nodes.append(
            GraphNode(
                id="n_github",
                label=f"GitHub @{gh.login}",
                type="github",
                weight=w_code,
                metadata=gh.model_dump(mode="json"),
            ),
        )
        nodes.append(
            GraphNode(
                id="n_code_metric",
                label="Code contribution cadence",
                type="metric",
                weight=w_code,
                metadata={
                    "index": round(w_code, 4),
                    "contributions_proxy": gh.contributions_last_year,
                    "source": gh.data_source,
                },
            ),
        )
        edges.append(GraphEdge(source="n_candidate", target="n_github", relation="github_profile", weight=1.0))
        edges.append(GraphEdge(source="n_github", target="n_code_metric", relation="activity_to_index", weight=w_code))

    academic_graphworthy = ac and (
        ac.cited_by_count
        or ac.works_count
        or ac.top_papers
        or ac.openalex_author_id
        or ac.semantic_scholar_author_id
    )
    if academic_graphworthy:
        w_cite = citation_impact_index(ac.cited_by_count)
        nodes.append(
            GraphNode(
                id="n_academic",
                label=f"Academic profile: {ac.display_name or label_name}",
                type="academic",
                weight=w_cite,
                metadata=ac.model_dump(mode="json"),
            ),
        )
        nodes.append(
            GraphNode(
                id="n_cite_metric",
                label="Publication citation impact",
                type="metric",
                weight=w_cite,
                metadata={
                    "index": round(w_cite, 4),
                    "cited_by_count": ac.cited_by_count,
                    "works_count": ac.works_count,
                    "h_index": ac.h_index,
                },
            ),
        )
        edges.append(
            GraphEdge(
                source="n_candidate",
                target="n_academic",
                relation="estimated_academic_profile",
                weight=0.75 if ac.identity_match == "name_search" else 0.35,
            ),
        )
        edges.append(GraphEdge(source="n_academic", target="n_cite_metric", relation="citations_to_index", weight=w_cite))

    if google_scholar_url and google_scholar_url.strip():
        nodes.append(
            GraphNode(
                id="n_scholar_claim",
                label="Google Scholar (claimed URL)",
                type="reference_link",
                weight=0.25,
                metadata={"url": google_scholar_url.strip(), "verified": False},
            ),
        )
        edges.append(
            GraphEdge(
                source="n_candidate",
                target="n_scholar_claim",
                relation="claimed_profile_url",
                weight=0.25,
            ),
        )

    graph = CapabilityOverviewGraph(nodes=nodes, edges=edges)
    return BackgroundAnalysisResult(
        candidate_name=candidate_name.strip() if candidate_name and candidate_name.strip() else None,
        github=gh,
        academic=ac,
        graph=graph,
    )
