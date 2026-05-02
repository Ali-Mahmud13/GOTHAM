"""Redact sensitive substrings before logging."""

import re

_PATTERNS = (
    (re.compile(r"(?i)(password|token|secret)\s*[:=]\s*\S+"), r"\1=***"),
    (re.compile(r"(?i)bearer\s+\S+"), "Bearer ***"),
)


def redact_message(msg: str, max_len: int = 500) -> str:
    if not msg:
        return ""
    out = str(msg)[:max_len]
    for pat, repl in _PATTERNS:
        out = pat.sub(repl, out)
    return out
