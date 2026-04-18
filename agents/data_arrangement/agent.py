"""使用大模型结构化输出将 OCR 文本映射为 ResumeStructuredProfile。"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from hiring_agent import config
from hiring_agent.agents.data_arrangement.models import ResumeStructuredProfile
from hiring_agent.agents.data_arrangement.prompts import DATA_ARRANGEMENT_SYSTEM
from hiring_agent.fairness.injection_sanitize import sanitize_resume_text

_MAX_OCR_CHARS = 100_000


def _truncate(text: str) -> tuple[str, bool]:
    if len(text) <= _MAX_OCR_CHARS:
        return text, False
    return text[:_MAX_OCR_CHARS], True


def arrange_resume_from_ocr_text(
    ocr_text: str,
) -> tuple[ResumeStructuredProfile, bool, dict[str, object]]:
    """
    语义解析 OCR 文本 -> 结构化履历。

    返回 (profile, truncated, injection_sanitize_meta)；
    truncated 表示因长度上限截断了输入；meta 为 Prompt Injection 清理统计。
    """
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set; Data Arrangement Agent cannot run")

    cleaned, inj_meta = sanitize_resume_text(ocr_text.strip() or "")
    body, truncated = _truncate(cleaned)
    if not body:
        return ResumeStructuredProfile(), truncated, inj_meta

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=config.OPENAI_API_KEY,
    ).with_structured_output(ResumeStructuredProfile)

    msg = HumanMessage(
        content=f"The following Markdown was produced by resume OCR. Extract and return the structured profile:\n\n{body}",
    )
    out = llm.invoke([SystemMessage(content=DATA_ARRANGEMENT_SYSTEM), msg])
    if isinstance(out, ResumeStructuredProfile):
        return out, truncated, inj_meta
    if isinstance(out, dict):
        return ResumeStructuredProfile.model_validate(out), truncated, inj_meta
    raise TypeError("structured_output returned an unexpected type")
