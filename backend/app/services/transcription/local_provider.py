"""Local faster-whisper provider.

Singleton WhisperModel kept warm in RAM. Decodes audio via the bundled PyAV
(no system ffmpeg required) and runs the sync transcribe() inside
asyncio.to_thread so the FastAPI event loop stays responsive.

Default model is `large-v3-turbo` int8 (~1.5 GB, ~2 GB RAM, ~3-8 s for a 10 s
clip on a modern i7 CPU). See backend/app/core/config.py for the full
trade-off table.
"""

from __future__ import annotations

import asyncio
import io
import logging
from threading import Lock
from typing import Optional

from app.core import config

logger = logging.getLogger(__name__)

_model = None
_model_lock = Lock()


def _get_model():
    """Lazy singleton — only loads the model on first transcription request."""
    global _model
    if _model is not None:
        return _model

    with _model_lock:
        if _model is not None:
            return _model

        # Imported lazily so the (heavy) ctranslate2 / faster-whisper deps
        # are only pulled in when the local provider is actually used.
        from faster_whisper import WhisperModel  # type: ignore

        logger.info(
            "Loading faster-whisper model '%s' (device=%s, compute_type=%s) — "
            "first request after startup will be slower while the model loads.",
            config.WHISPER_MODEL,
            config.WHISPER_DEVICE,
            config.WHISPER_COMPUTE_TYPE,
        )
        _model = WhisperModel(
            config.WHISPER_MODEL,
            device=config.WHISPER_DEVICE,
            compute_type=config.WHISPER_COMPUTE_TYPE,
        )
        logger.info("faster-whisper model loaded.")
        return _model


def _transcribe_sync(audio_bytes: bytes, language: Optional[str]) -> dict:
    """Run inside asyncio.to_thread — no event-loop access."""
    model = _get_model()
    segments, info = model.transcribe(
        io.BytesIO(audio_bytes),
        language=language,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        beam_size=5,
        condition_on_previous_text=False,
    )
    text_parts = [seg.text.strip() for seg in segments if seg.text and seg.text.strip()]
    text = " ".join(text_parts).strip()
    duration_seconds = float(getattr(info, "duration", 0.0) or 0.0)
    detected_language = getattr(info, "language", language) or language or "en"

    return {
        "text": text,
        "language": detected_language,
        "duration_ms": int(duration_seconds * 1000),
    }


async def transcribe(
    audio_bytes: bytes,
    language: str = "en",
    mime_type: str = "audio/webm",  # accepted for signature parity with groq_provider
) -> dict:
    """Transcribe audio locally via faster-whisper.

    Args:
        audio_bytes: raw audio file bytes (any format ffmpeg can decode).
        language: ISO-639-1 code. Use "en" for English, "ur" for Urdu / Minglish.
        mime_type: ignored here; kept for interface parity with groq_provider.

    Returns:
        {"text": str, "language": str, "duration_ms": int}
    """
    return await asyncio.to_thread(_transcribe_sync, audio_bytes, language)
