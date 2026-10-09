"""Small security helpers; never execute arbitrary user-provided code."""
from __future__ import annotations

import re


def clean_user_text(value: str, limit: int = 4000) -> str:
    """Normalize user text and limit its length."""
    value = (value or "").replace("\x00", "").strip()
    return value[: max(1, limit)]


def looks_like_secret(value: str) -> bool:
    """Best-effort warning detector; not a replacement for secret scanning."""
    patterns = (
        r"sk-[A-Za-z0-9_-]{16,}",
        r"(?i)bot\d{6,}:[A-Za-z0-9_-]{20,}",
        r"(?i)(api[_-]?key|password|secret)\s*[:=]\s*\S+",
    )
    return any(re.search(pattern, value or "") for pattern in patterns)
