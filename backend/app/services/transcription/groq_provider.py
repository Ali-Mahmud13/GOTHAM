"""Groq Whisper API provider.

Sends audio bytes to Groq's hosted Whisper-large-v3 (or v3-turbo) and returns
the transcribed text. Free tier: 7,200 audio seconds/day. Sub-second typical
latency for clinical-length dictation.
"""

from __future__ import annotations

import logging
from typing import Optional

from groq import AsyncGroq

from app.core import config

logger = logging.getLogger(__name__)

_client: Optional[AsyncGroq] = None


def _get_client() -> AsyncGroq:
    """Lazy singleton — only constructed if Groq is actually used."""
    global _client
    if _client is None:
        if not config.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Either configure it in backend/.env "
                "or set STT_PROVIDER=local to use the on-prem fallback."
            )
        _client = AsyncGroq(api_key=config.GROQ_API_KEY)
    return _client


async def transcribe(
    audio_bytes: bytes,
    language: str = "en",
    mime_type: str = "audio/webm",
) -> dict:
    """Transcribe audio via Groq's hosted Whisper API.

    Args:
        audio_bytes: raw audio file bytes (webm/opus, wav, mp3 etc.)
        language: ISO-639-1 code. "en" for English, "ur" for Urdu / Minglish.
        mime_type: MIME type of the audio (used for filename hint to Groq).

    Returns:
        {"text": str, "language": str, "duration_ms": int}

    Raises:
        groq.RateLimitError: 429 when daily quota exhausted
        groq.APIConnectionError: network failure
        groq.AuthenticationError: bad API key
    """
    client = _get_client()
    extension = _ext_for_mime(mime_type)

    response = await client.audio.transcriptions.create(
        file=(f"audio.{extension}", audio_bytes, mime_type),
        model=config.GROQ_WHISPER_MODEL,
        language=language,
        response_format="verbose_json",
        temperature=0.0,
    )

    text = (response.text or "").strip()
    duration_seconds = float(getattr(response, "duration", 0.0) or 0.0)
    detected_language = getattr(response, "language", language) or language

    return {
        "text": text,
        "language": detected_language,
        "duration_ms": int(duration_seconds * 1000),
    }


def _ext_for_mime(mime_type: str) -> str:
    """Map MIME type to a file extension Groq's API expects in the filename."""
    mapping = {
        "audio/webm": "webm",
        "audio/ogg": "ogg",
        "audio/wav": "wav",
        "audio/wave": "wav",
        "audio/x-wav": "wav",
        "audio/mpeg": "mp3",
        "audio/mp3": "mp3",
        "audio/mp4": "m4a",
        "audio/m4a": "m4a",
        "audio/flac": "flac",
    }
    base = (mime_type or "").split(";")[0].strip().lower()
    return mapping.get(base, "webm")
