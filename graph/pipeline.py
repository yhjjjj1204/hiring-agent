"""有状态招聘主工作流：HR 需求 -> OCR -> 数据排列 -> 背调 -> 自动评分 + HITL。"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from hiring_agent import config
from hiring_agent.agents.background_analysis.agent import run_background_analysis
from hiring_agent.agents.data_arrangement.agent import arrange_resume_from_ocr_text
from hiring_agent.agents.data_arrangement.models import ResumeStructuredProfile
from hiring_agent.agents.hr_strategy.models import HRJobSpec
from hiring_agent.agents.scoring.agent import score_match
from hiring_agent.agents.scoring.models import Scorecard
from hiring_agent.fairness.blind_screening import (
    blind_screen_background_for_scoring,
    blind_screen_resume_profile,
)
from hiring_agent.fairness.injection_sanitize import sanitize_resume_text
from hiring_agent.monitoring.pipeline_hooks import monitored_node
from hiring_agent.agents.ocr_agent import extract_and_arrange_resume_from_path

logger = logging.getLogger(__name__)

_CONFIDENCE_HITL_THRESHOLD = 0.55
_MIN_HR_CHARS = 15
_PIPELINE_BUILD_ID = 4  # 图结构变更时递增以失效旧编译缓存


class HiringPipelineState(TypedDict, total=False):
    """LangGraph 主状态；各节点写入对应键。HITL 通过 interrupt 返回的 resume 值合并逻辑。"""

    job_spec: dict[str, Any] | None
    hr_requirement_text: str | None

    resume_path: str | None
    resume_ocr_text: str | None
    ocr_text: str | None
    arrange_ocr_was_truncated: bool | None

    arranged_resume: dict[str, Any] | None

    candidate_github: str | None
    google_scholar_url: str | None
    candidate_name_override: str | None

    background_result: dict[str, Any] | None
    arranged_resume_blinded: dict[str, Any] | None
    background_result_blinded: dict[str, Any] | None
    scorecard: dict[str, Any] | None
    candidate_ref: str | None

    pipeline_status: str
    last_error: str | None
    fairness_injection_meta: dict[str, Any] | None


def extract_hr_job_spec_from_text(hr_requirement_text: str) -> dict[str, Any]:
    """从 HR 自由文本抽取结构化岗位说明（同步评析等场景复用，不经 HITL）。"""
    text = (hr_requirement_text or "").strip()
    if len(text) < _MIN_HR_CHARS:
        raise ValueError(f"Job description is too short; provide at least {_MIN_HR_CHARS} non-whitespace characters")
    spec = _llm_extract_hr_job_spec(text)
    return spec.model_dump(mode="json")


def _llm_extract_hr_job_spec(text: str) -> HRJobSpec:
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=config.OPENAI_API_KEY,
    ).with_structured_output(HRJobSpec)
    msg = HumanMessage(
        content=(
            "The following text is an HR job description. Extract a complete HRJobSpec "
            "(required skills, bonus items, and culture-fit metrics must all be present).\n\n"
            f"{text}"
        ),
    )
    out = llm.invoke(
        [
            SystemMessage(
                content=(
                    "You specialize in structuring hiring briefs. If information is thin, infer conservatively "
                    "and state assumptions in summary; never leave required lists empty."
                )
            ),
            msg,
        ],
    )
    if isinstance(out, HRJobSpec):
        return out
    if isinstance(out, dict):
        return HRJobSpec.model_validate(out)
    raise TypeError("HRJobSpec structured_output returned an unexpected type")


def _arrange_ambiguity_reason(profile: ResumeStructuredProfile, ocr_len: int) -> str | None:
    if ocr_len < 120:
        return None
    if not profile.skills and not profile.experience and not profile.education:
        return (
            "OCR text is long but no education, experience, or skills were parsed; "
            "check scan quality or layout."
        )
    if len(profile.experience) == 0 and len(profile.skills) < 2 and ocr_len > 600:
        return "Long text but almost no work history or skills; parsing may be unreliable."
    return None


def _name_background_mismatch(arr: dict[str, Any], bg: dict[str, Any]) -> str | None:
    cn = (arr.get("candidate_name") or "").strip()
    ac = (bg.get("academic") or {}) if isinstance(bg.get("academic"), dict) else {}
    dn = (ac.get("display_name") or "").strip()
    if not cn or not dn:
        return None
    if cn.replace(" ", "").lower() == dn.replace(" ", "").lower():
        return None
    # 简单拉丁/中文混排不展开 NLP；仅提示人工
    if cn not in dn and dn not in cn:
        return (
            f"Resume name «{cn}» does not match academic profile display name «{dn}»; "
            "possible homonym or wrong match."
        )
    return None


def node_hr_ingest(state: HiringPipelineState) -> dict[str, Any]:
    if state.get("job_spec"):
        return {"pipeline_status": "running"}

    text = (state.get("hr_requirement_text") or "").strip()
    if len(text) < _MIN_HR_CHARS:
        fb = interrupt(
            {
                "kind": "hitl",
                "stage": "hr_requirement",
                "message": "Job description is too short or missing; cannot build a reliable structured spec.",
                "instructions": (
                    "On the next resume, provide either "
                    "1) a longer plain-text `hr_requirement_text`, or "
                    "2) a full `job_spec` JSON object shaped like HRJobSpec."
                ),
            },
        )
        if isinstance(fb, dict) and isinstance(fb.get("job_spec"), dict):
            spec = HRJobSpec.model_validate(fb["job_spec"])
            return {"job_spec": spec.model_dump(mode="json"), "pipeline_status": "running"}
        if isinstance(fb, dict) and isinstance(fb.get("hr_requirement_text"), str):
            text = fb["hr_requirement_text"].strip()
        elif isinstance(fb, str):
            text = (text + "\n" + fb).strip()

    if len(text) < _MIN_HR_CHARS:
        return {
            "last_error": "hr_requirement_still_insufficient",
            "pipeline_status": "failed",
        }

    spec = _llm_extract_hr_job_spec(text)
    return {
        "job_spec": spec.model_dump(mode="json"),
        "hr_requirement_text": text,
        "pipeline_status": "running",
    }


def _merge_fairness_meta(
    state: HiringPipelineState,
    key: str,
    meta: dict[str, Any],
) -> dict[str, Any]:
    prev = dict(state.get("fairness_injection_meta") or {})
    prev[key] = meta
    return prev


def node_resume_ocr(state: HiringPipelineState) -> dict[str, Any]:
    if state.get("ocr_text") and state.get("arranged_resume"):
        return {}

    if state.get("resume_ocr_text"):
        raw = state["resume_ocr_text"].strip()
        safe, meta = sanitize_resume_text(raw)
        return {
            "ocr_text": safe,
            "fairness_injection_meta": _merge_fairness_meta(state, "resume_ocr_input", meta),
        }

    path = state.get("resume_path")
    if path and Path(path).is_file():
        try:
            parsed = extract_and_arrange_resume_from_path(path)
            safe, meta = sanitize_resume_text(parsed.ocr_text)
            return {
                "ocr_text": safe,
                "arranged_resume": parsed.arranged_profile.model_dump(mode="json"),
                "arrange_ocr_was_truncated": False,
                "fairness_injection_meta": _merge_fairness_meta(state, "resume_ocr_file", meta),
            }
        except Exception as e:
            logger.warning("Resume OCR failed: %s", e)
            fb = interrupt(
                {
                    "kind": "hitl",
                    "stage": "resume_ocr",
                    "message": f"Resume OCR failed: {e}",
                    "instructions": "In resume, provide `resume_ocr_text` (Markdown paste) or fix `resume_path` and retry.",
                },
            )
            if isinstance(fb, dict) and isinstance(fb.get("resume_ocr_text"), str):
                raw_fb = fb["resume_ocr_text"].strip()
                sfb, mfb = sanitize_resume_text(raw_fb)
                return {
                    "ocr_text": sfb,
                    "fairness_injection_meta": _merge_fairness_meta(state, "resume_ocr_hitl", mfb),
                }
            if isinstance(fb, dict) and isinstance(fb.get("resume_path"), str) and Path(fb["resume_path"]).is_file():
                parsed = extract_and_arrange_resume_from_path(fb["resume_path"])
                safe, meta = sanitize_resume_text(parsed.ocr_text)
                return {
                    "ocr_text": safe,
                    "arranged_resume": parsed.arranged_profile.model_dump(mode="json"),
                    "arrange_ocr_was_truncated": False,
                    "resume_path": fb["resume_path"],
                    "fairness_injection_meta": _merge_fairness_meta(state, "resume_ocr_hitl_file", meta),
                }
            return {"last_error": "ocr_unresolved", "pipeline_status": "failed"}

    fb = interrupt(
        {
            "kind": "hitl",
            "stage": "resume_ocr",
            "message": "Resume OCR input is missing.",
            "instructions": "Provide a server-readable `resume_path`, or provide `resume_ocr_text` directly.",
        },
    )
    if isinstance(fb, dict) and isinstance(fb.get("resume_ocr_text"), str):
        raw_fb = fb["resume_ocr_text"].strip()
        sfb, mfb = sanitize_resume_text(raw_fb)
        return {
            "ocr_text": sfb,
            "fairness_injection_meta": _merge_fairness_meta(state, "resume_ocr_hitl_initial", mfb),
        }
    if isinstance(fb, dict) and isinstance(fb.get("resume_path"), str) and Path(fb["resume_path"]).is_file():
        parsed = extract_and_arrange_resume_from_path(fb["resume_path"])
        safe, meta = sanitize_resume_text(parsed.ocr_text)
        return {
            "ocr_text": safe,
            "arranged_resume": parsed.arranged_profile.model_dump(mode="json"),
            "arrange_ocr_was_truncated": False,
            "resume_path": fb["resume_path"],
            "fairness_injection_meta": _merge_fairness_meta(state, "resume_ocr_hitl_initial_file", meta),
        }
    return {"last_error": "missing_resume_input", "pipeline_status": "failed"}


def node_resume_arrange(state: HiringPipelineState) -> dict[str, Any]:
    if state.get("arranged_resume"):
        return {"pipeline_status": "running"}

    ocr = (state.get("ocr_text") or "").strip()
    if not ocr:
        return {"last_error": "empty_ocr", "pipeline_status": "failed"}

    profile, truncated, inj_meta = arrange_resume_from_ocr_text(ocr)
    reason = _arrange_ambiguity_reason(profile, len(ocr))
    if reason:
        fb = interrupt(
            {
                "kind": "hitl",
                "stage": "resume_arrange",
                "message": reason,
                "draft_profile": profile.model_dump(mode="json"),
                "instructions": (
                    'To accept the draft: `{"action":"accept_draft","draft_profile": ...}`; '
                    "to replace OCR: send full `resume_ocr_text`."
                ),
            },
        )
        if isinstance(fb, dict):
            if fb.get("action") == "accept_draft" and isinstance(fb.get("draft_profile"), dict):
                p2 = ResumeStructuredProfile.model_validate(fb["draft_profile"])
                return {
                    "arranged_resume": p2.model_dump(mode="json"),
                    "arrange_ocr_was_truncated": truncated,
                    "fairness_injection_meta": _merge_fairness_meta(state, "arrange_pass", inj_meta),
                    "pipeline_status": "running",
                }
            if isinstance(fb.get("resume_ocr_text"), str):
                ocr2 = fb["resume_ocr_text"].strip()
                s2, m_ocr2 = sanitize_resume_text(ocr2)
                p2, t2, inj2 = arrange_resume_from_ocr_text(s2)
                return {
                    "ocr_text": s2,
                    "arranged_resume": p2.model_dump(mode="json"),
                    "arrange_ocr_was_truncated": t2,
                    "fairness_injection_meta": {
                        **(state.get("fairness_injection_meta") or {}),
                        "arrange_pass": inj2,
                        "resume_ocr_replaced_hitl": m_ocr2,
                    },
                    "pipeline_status": "running",
                }

    return {
        "arranged_resume": profile.model_dump(mode="json"),
        "arrange_ocr_was_truncated": truncated,
        "fairness_injection_meta": _merge_fairness_meta(state, "arrange_pass", inj_meta),
        "pipeline_status": "running",
    }


def node_background(state: HiringPipelineState) -> dict[str, Any]:
    arr = state.get("arranged_resume") or {}
    name = (arr.get("candidate_name") or "").strip() or (state.get("candidate_name_override") or "").strip() or None
    gh = state.get("candidate_github")
    scholar = state.get("google_scholar_url")

    result = run_background_analysis(name, gh, scholar)
    payload = result.model_dump(mode="json")
    mismatch = _name_background_mismatch(arr, payload)
    if mismatch:
        # 开发/批处理场景下，学术检索存在同名误匹配时不应卡住流水线；
        # 直接丢弃 academic 分支并继续评分（评分本身使用盲审快照）。
        safe_payload = dict(payload)
        safe_payload["academic"] = {}
        safe_payload["academic_dropped_reason"] = mismatch
        return {"background_result": safe_payload, "pipeline_status": "running"}

    return {"background_result": payload, "pipeline_status": "running"}


def node_fairness_blinding(state: HiringPipelineState) -> dict[str, Any]:
    """盲审：生成仅用于评分的脱敏快照（完整履历仍在 arranged_resume 供背调等使用）。"""
    arr = state.get("arranged_resume") or {}
    bg = state.get("background_result") or {}
    if not arr:
        return {}
    return {
        "arranged_resume_blinded": blind_screen_resume_profile(arr),
        "background_result_blinded": blind_screen_background_for_scoring(bg),
    }


def node_auto_score(state: HiringPipelineState) -> dict[str, Any]:
    job = state.get("job_spec") or {}
    arr = state.get("arranged_resume_blinded") or blind_screen_resume_profile(state.get("arranged_resume") or {})
    bg = state.get("background_result_blinded") or blind_screen_background_for_scoring(
        state.get("background_result") or {},
    )

    sc = score_match(job, arr, bg)
    low = sc.overall_confidence < _CONFIDENCE_HITL_THRESHOLD or sc.hitl_suggested
    if low:
        fb = interrupt(
            {
                "kind": "hitl",
                "stage": "auto_score",
                "message": "Automatic score confidence is low or the case is ambiguous; HR decision needed.",
                "draft_scorecard": sc.model_dump(mode="json"),
                "hitl_reason": sc.hitl_reason,
                "instructions": (
                    'To accept the draft scorecard, resume with: '
                    '`{"action":"accept_draft","draft_scorecard": <same or edited JSON>}`'
                ),
            },
        )
        if isinstance(fb, dict) and fb.get("action") == "accept_draft" and isinstance(fb.get("draft_scorecard"), dict):
            card = Scorecard.model_validate(fb["draft_scorecard"])
            return {"scorecard": card.model_dump(mode="json"), "pipeline_status": "completed"}

    return {"scorecard": sc.model_dump(mode="json"), "pipeline_status": "completed"}


_checkpointer = InMemorySaver()
_compiled = None
_compiled_build_id: int | None = None


def build_hiring_pipeline_graph():
    """编译带 checkpoint 的主工作流（内存；生产可换 PostgresSaver）。"""
    global _compiled, _compiled_build_id
    if _compiled is not None and _compiled_build_id == _PIPELINE_BUILD_ID:
        return _compiled

    graph = StateGraph(HiringPipelineState)
    graph.add_node("hr_ingest", monitored_node("hr_ingest", node_hr_ingest))
    graph.add_node("resume_ocr", monitored_node("resume_ocr", node_resume_ocr))
    graph.add_node("resume_arrange", monitored_node("resume_arrange", node_resume_arrange))
    graph.add_node("background_analysis", monitored_node("background_analysis", node_background))
    graph.add_node("fairness_blinding", monitored_node("fairness_blinding", node_fairness_blinding))
    graph.add_node("auto_score", monitored_node("auto_score", node_auto_score))

    graph.add_edge(START, "hr_ingest")
    graph.add_edge("hr_ingest", "resume_ocr")
    graph.add_edge("resume_ocr", "resume_arrange")
    graph.add_edge("resume_arrange", "background_analysis")
    graph.add_edge("background_analysis", "fairness_blinding")
    graph.add_edge("fairness_blinding", "auto_score")
    graph.add_edge("auto_score", END)

    _compiled = graph.compile(checkpointer=_checkpointer)
    _compiled_build_id = _PIPELINE_BUILD_ID
    return _compiled


def pipeline_config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}


def extract_interrupts(result: dict[str, Any]) -> list[dict[str, Any]]:
    raw = result.get("__interrupt__") or ()
    out: list[dict[str, Any]] = []
    for item in raw:
        if hasattr(item, "value"):
            out.append({"id": getattr(item, "id", None), "value": item.value})
        else:
            out.append({"value": item})
    return out
