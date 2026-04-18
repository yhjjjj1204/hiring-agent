"""简历 OCR / 纯文本中的 Prompt Injection 清理（启发式，非 LLM）。"""

from __future__ import annotations

import re
from typing import Any

# 常见注入/越狱指令片段（大小写不敏感）
_INJECTION_LINE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(ignore|disregard)\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts?|rules?)",
        re.I,
    ),
    re.compile(r"你(现在|必须|请)(忽略|忘掉).*(指令|规则|上文)", re.I),
    re.compile(r"(new|system)\s*instructions?\s*[:：]", re.I),
    re.compile(r"<\s*/?\s*system\s*>", re.I),
    re.compile(r"<\|[^|]+\|>", re.I),  # ChatML / 特殊 token 风格
    re.compile(r"\bDAN\b.*\bmode\b", re.I),
    re.compile(r"jailbreak", re.I),
    re.compile(r"override\s+(safety|policy|rules?)", re.I),
    re.compile(r"输出\s*(隐藏|内部|原始)\s*(prompt|指令|system)", re.I),
    re.compile(r"repeat\s+(the\s+)?(system\s+)?prompt", re.I),
    re.compile(r"```\s*(system|assistant)\s*", re.I),
    re.compile(r"###\s*(system|assistant|instruction)", re.I),
)

# 整块删除：疑似把整段简历替换成“指令文档”的标题行
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
    按行扫描并剔除高风险注入行；保留其余内容结构。

    返回 (清理后文本, 元数据统计)。
    """
    if not text:
        return "", {"lines_removed": 0, "chars_removed": 0}

    lines = text.splitlines(keepends=True)
    out_lines: list[str] = []
    removed = 0
    removed_chars = 0
    for line in lines:
        # 按物理行处理；\r\n 保留在 line 内
        core = line.rstrip("\r\n")
        suffix = line[len(core) :]
        scrubbed = _scrub_line(core)
        if scrubbed is None:
            removed += 1
            removed_chars += len(line)
            continue
        out_lines.append(scrubbed + suffix)

    cleaned = "".join(out_lines)
    # 折叠连续空行（最多保留两个换行）
    cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned)
    meta: dict[str, Any] = {
        "lines_removed": removed,
        "chars_removed": removed_chars,
        "sanitizer": "injection_sanitize_v1",
    }
    return cleaned, meta


def sanitize_for_llm_user_content(text: str) -> str:
    """便捷封装：仅返回清理后字符串。"""
    return sanitize_resume_text(text)[0]
