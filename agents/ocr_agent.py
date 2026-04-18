"""基于 OpenAI GPT-4o 的简历 OCR + 结构化解析 Agent。"""

from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, Field

from hiring_agent import config
from hiring_agent.agents.data_arrangement.models import ResumeStructuredProfile

_ALLOWED_SUFFIXES = frozenset(
    {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".gif",
        ".bmp",
        ".tiff",
        ".tif",
    },
)


class ResumeOCRAndProfile(BaseModel):
    """Single-call output: OCR Markdown plus structured resume profile."""

    ocr_text: str = Field(default="", description="Resume content as Markdown extracted from the file")
    arranged_profile: ResumeStructuredProfile = Field(default_factory=ResumeStructuredProfile)


def is_supported_suffix(path: str | Path) -> bool:
    return Path(path).suffix.lower() in _ALLOWED_SUFFIXES


def is_allowed_upload_suffix(suffix: str) -> bool:
    s = (suffix or "").lower().strip()
    if not s:
        return False
    if not s.startswith("."):
        s = f".{s}"
    return s in _ALLOWED_SUFFIXES


def _require_openai_key() -> str:
    key = config.OPENAI_API_KEY
    if not key:
        raise ValueError("OPENAI_API_KEY is not set. Configure it in the environment or .env file.")
    return key


def _to_data_url(path: Path) -> tuple[str, str]:
    mime, _ = mimetypes.guess_type(path.name)
    if not mime:
        if path.suffix.lower() == ".pdf":
            mime = "application/pdf"
        else:
            mime = "image/png"
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return mime, f"data:{mime};base64,{b64}"


def _build_user_content(path: Path) -> list[dict[str, Any]]:
    mime, data_url = _to_data_url(path)
    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "Read this resume file carefully, then perform the requested task. "
                "If information is missing, use empty strings, null, or empty arrays; do not invent facts."
            ),
        },
    ]
    if mime.startswith("image/"):
        content.append({"type": "image_url", "image_url": {"url": data_url}})
        return content
    if mime == "application/pdf":
        content.append(
            {
                "type": "file",
                "file": {
                    "filename": path.name,
                    "file_data": data_url,
                },
            },
        )
        return content
    raise ValueError(f"Unsupported file MIME type: {mime}")


def _chat_completion(
    path: Path,
    user_task: str,
    response_format: dict[str, Any] | None = None,
) -> str:
    if not path.is_file():
        raise FileNotFoundError(str(path))
    if not is_supported_suffix(path):
        raise ValueError(f"Unsupported file type: {path.suffix}")

    client = OpenAI(api_key=_require_openai_key())
    kwargs: dict[str, Any] = {
        "model": "gpt-4o",
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": "You are a resume parsing assistant in a hiring system. Be stable, factual, and reproducible.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_task},
                    *_build_user_content(path),
                ],
            },
        ],
    }
    if response_format is not None:
        kwargs["response_format"] = response_format
    resp = client.chat.completions.create(**kwargs)
    content = (resp.choices[0].message.content or "").strip()
    if not content:
        raise RuntimeError("OpenAI returned empty content")
    return content


def extract_resume_text_from_path(file_path: str | Path) -> str:
    """读取图片/PDF 简历并提取 Markdown 文本。"""
    path = Path(file_path)
    return _chat_completion(
        path=path,
        user_task=(
            "Transcribe the resume into Markdown. Rules: "
            "1) Do not summarize or paraphrase; 2) Preserve structure and key points; "
            "3) Output Markdown body only."
        ),
    )


def extract_and_arrange_resume_from_path(
    file_path: str | Path,
) -> ResumeOCRAndProfile:
    """一次调用完成 OCR 与结构化履历解析。"""
    path = Path(file_path)
    schema_text = json.dumps(ResumeOCRAndProfile.model_json_schema(), ensure_ascii=False)
    content = _chat_completion(
        path=path,
        user_task=(
            "Do both in one response: "
            "1) Extract the full resume as Markdown into ocr_text; "
            "2) Output the structured profile into arranged_profile per the JSON Schema below. "
            "Return a single JSON object whose fields strictly match this schema:\n"
            f"{schema_text}"
        ),
        response_format={"type": "json_object"},
    )
    payload = json.loads(content)
    return ResumeOCRAndProfile.model_validate(payload)
