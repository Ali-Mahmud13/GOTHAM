"""Speech-to-text dispatcher.

Provides a single `transcribe()` entry point that routes to the configured
provider (Groq cloud or local faster-whisper) based on `STT_PROVIDER`. When
provider is "auto", Groq is tried first and we transparently fall back to the
local model on rate-limit / network / auth errors so the doctor's mic never
just stops working.
"""

from __future__ import annotations

import logging
from typing import Optional

from groq import APIConnectionError, AuthenticationError, RateLimitError, GroqError

from app.core import config
from app.services.transcription import groq_provider, local_provider

logger = logging.getLogger(__name__)


# Errors that should trigger the auto-fallback (recoverable cloud failures).
_RECOVERABLE_GROQ_ERRORS: tuple[type[Exception], ...] = (
    RateLimitError,
    APIConnectionError,
    AuthenticationError,
    GroqError,
)


async def transcribe(
    audio_bytes: bytes,
    language: str = "en",
    mime_type: str = "audio/webm",
) -> dict:
    """Transcribe audio using the configured provider.

    Args:
        audio_bytes: raw audio file bytes (typically webm/opus from MediaRecorder).
        language: ISO-639-1 code. "en" = English, "ur" = Urdu (use "ur" for Minglish).
        mime_type: MIME type of the audio blob.

    Returns:
        {
          "text": str,
          "language": str,
          "duration_ms": int,
          "provider_used": "groq" | "local"
        }
    """
    provider = (config.STT_PROVIDER or "auto").lower()

    if provider in ("groq", "auto"):
        try:
            result = await groq_provider.transcribe(audio_bytes, language, mime_type)
            result["provider_used"] = "groq"
            return result
        except _RECOVERABLE_GROQ_ERRORS as exc:
            if provider == "groq":
                # Explicit groq-only -> bubble up so caller sees the real error
                raise
            logger.warning(
                "Groq transcription failed (%s), falling back to local Whisper.",
                exc.__class__.__name__,
            )
        except RuntimeError as exc:
            # e.g. missing GROQ_API_KEY when STT_PROVIDER=auto
            if provider == "groq":
                raise
            logger.warning(
                "Groq provider unavailable (%s), falling back to local Whisper.",
                exc,
            )

    result = await local_provider.transcribe(audio_bytes, language, mime_type)
    result["provider_used"] = "local"
    return result


__all__ = ["transcribe"]
