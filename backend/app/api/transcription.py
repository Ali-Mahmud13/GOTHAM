"""Voice dictation transcription endpoint."""

import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Request
from app.core.rate_limit import limiter

from app.core import config
from app.services import transcription as transcription_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["transcription"])


# Languages we explicitly support today. Whisper supports many more, but we
# guard the input so accidental typos don't degrade results silently.
_ALLOWED_LANGUAGES = {"en", "ur"}


@router.post("/transcribe")
@limiter.limit("10/minute")
async def transcribe_audio(
    request: Request,
    audio: UploadFile = File(...),
    language: str = Form("en"),
):
    """Transcribe a single audio file (press-to-talk dictation).

    Routed via `services.transcription` which dispatches to Groq cloud
    (default, sub-second) with automatic fallback to local faster-whisper
    on rate-limit / network failure.

    Form fields:
        audio: audio blob (typically webm/opus from MediaRecorder).
        language: "en" (English) or "ur" (Urdu / Minglish).

    Returns:
        {
          "text": str,
          "language": str,
          "duration_ms": int,
          "provider_used": "groq" | "local"
        }
    """
    lang = (language or "en").lower().strip()
    if lang not in _ALLOWED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language '{language}'. Allowed: {sorted(_ALLOWED_LANGUAGES)}",
        )

    audio_bytes = await audio.read()

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio payload")

    if len(audio_bytes) > config.TRANSCRIBE_MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Audio too large ({len(audio_bytes)} bytes). "
                f"Max allowed is {config.TRANSCRIBE_MAX_BYTES} bytes."
            ),
        )

    mime_type = audio.content_type or "audio/webm"

    try:
        result = await transcription_service.transcribe(
            audio_bytes=audio_bytes,
            language=lang,
            mime_type=mime_type,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 - we want to convert anything to 422 here
        logger.error("Transcription failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=422,
            detail=f"Failed to transcribe audio: {exc}",
        )

    return result
