"""Prompt Injection cleaning in resume OCR / plain text (heuristic, non-LLM)."""

from __future__ import annotations

import re
from typing import Any

# Common injection/jailbreak instruction snippets (case-insensitive)
_INJECTION_LINE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(ignore|disregard)\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts?|rules?)",
        re.I,
    ),
    re.compile(r"你(现在|必须|请)(忽略|忘掉).*(指令|规则|上文)", re.I),
    re.compile(r"(new|system)\s*instructions?\s*[:：]", re.I),
    re.compile(r"<\s*/?\s*system\s*>", re.I),
    re.compile(r"<\|[^|]+\|>", re.I),  # ChatML / special token style
    re.compile(r"\bDAN\b.*\bmode\b", re.I),
    re.compile(r"jailbreak", re.I),
    re.compile(r"override\s+(safety|policy|rules?)", re.I),
    re.compile(r"输出\s*(隐藏|内部|原始)\s*(prompt|指令|system)", re.I),
    re.compile(r"repeat\s+(the\s+)?(system\s+)?prompt", re.I),
    re.compile(r"```\s*(system|assistant)\s*", re.I),
    re.compile(r"###\s*(system|assistant|instruction)", re.I),
)

# Block removal: Header lines suspected of replacing resume sections with instruction sets
_SUSPICIOUS_HEADERS = re.compile(
    r"^\s*(system\s*prompt|developer\s*message|base\s*instructions|"
    r"工具\s*调用|function\s*call\s*schema|JSON\s*schema\s*for)\s*[:：]?\s*$",
    re.I | re.M,
)


def _scrub_line(line: str) -> str | None:
    s = line.strip()
    if not s:
        return line
    for pat in _INJECTION_LINE_PATTERNS:
        if pat.search(s):
            return None
    if _SUSPICIOUS_HEADERS.match(s):
        return None
    return line


def sanitize_resume_text(text: str) -> tuple[str, dict[str, Any]]:
    """
    Scan line by line and remove high-risk injection lines; preserve remaining structure.

    Returns (cleaned_text, metadata_stats).
    """
    if not text:
        return "", {"lines_removed": 0, "chars_removed": 0}

    lines = text.splitlines(keepends=True)
    out_lines: list[str] = []
    removed = 0
    removed_chars = 0
    for line in lines:
        # Process by physical line; \r\n is preserved in the line
        core = line.rstrip("\r\n")
        suffix = line[len(core) :]
        scrubbed = _scrub_line(core)
        if scrubbed is None:
            removed += 1
            removed_chars += len(line)
            continue
        out_lines.append(scrubbed + suffix)

    cleaned = "".join(out_lines)
    # Collapse consecutive empty lines (keep at most two newlines)
    cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned)
    meta: dict[str, Any] = {
        "lines_removed": removed,
        "chars_removed": removed_chars,
        "sanitizer": "injection_sanitize_v1",
    }
    return cleaned, meta


def sanitize_for_llm_user_content(text: str) -> str:
    """Convenience wrapper: returns only the cleaned string."""
    return sanitize_resume_text(text)[0]
