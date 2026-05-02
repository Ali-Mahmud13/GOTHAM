"""Note sanitization and prompt-injection hardening."""

import re
import bleach

_MAX_NOTE_LEN = 200_000


def sanitize_note(text: str) -> str:
    """Strip HTML / scripts, normalize whitespace, cap length for stored clinical text."""
    if not text:
        return ""
    cleaned = bleach.clean(text, tags=[], strip=True)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:_MAX_NOTE_LEN]


def safe_for_prompt(text: str) -> str:
    """Bound user-supplied text inside LLM prompts (escape fence breakouts)."""
    if not text:
        return ""
    t = text.replace("```", "`\u200b``")
    return t[:_MAX_NOTE_LEN]
