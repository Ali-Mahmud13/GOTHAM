"""Application configuration."""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database Settings
try:
    import sys

    _is_pytest = "pytest" in sys.modules
except Exception:
    _is_pytest = False

if _is_pytest:
    # Tests should not depend on an external Postgres/Neon URL from a developer .env.
    DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")
else:
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Please create a .env file in the backend/ directory with your Neon connection string. "
            "Example: DATABASE_URL=postgresql://user:pass@host/database"
        )

# LLM Settings
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # Kept for backward compatibility
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")

# Gemini Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

# OpenAI Settings (Primary LLM)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

# LLM Provider Selection (openai, groq, gemini)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

# Model used only for /api/notes/parse (structured JSON extraction).
# IMPORTANT: the model id must match the configured provider.
# - For groq: use llama-3.3-70b-versatile (most reliable JSON)
# - For openai: default to OPENAI_MODEL_NAME
# - For gemini: default to GEMINI_MODEL_NAME
_DEFAULT_EXTRACTION_MODEL = (
    "llama-3.3-70b-versatile"
    if LLM_PROVIDER.lower() == "groq"
    else (OPENAI_MODEL_NAME if LLM_PROVIDER.lower() == "openai" else GEMINI_MODEL_NAME)
)
EXTRACTION_MODEL = os.getenv("EXTRACTION_MODEL", _DEFAULT_EXTRACTION_MODEL)

# ─── Speech-to-Text (Voice Dictation) ────────────────────────────────────────
# Provider:
#   "auto"  -> try Groq first (sub-second), fall back to local on rate-limit / error
#   "groq"  -> Groq only (raise on error)
#   "local" -> local faster-whisper only (100% private, no audio leaves the server)
STT_PROVIDER = os.getenv("STT_PROVIDER", "auto").lower()

# Groq Whisper model (used by Groq path).
#   "whisper-large-v3"        -> best quality
#   "whisper-large-v3-turbo"  -> faster, slightly lower quality
GROQ_WHISPER_MODEL = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3")

# Local faster-whisper model (used when STT_PROVIDER="local" or as fallback).
#   "small"             -> fast, weak Urdu / Minglish (~480 MB)
#   "medium"            -> slower, decent Urdu (~770 MB)
#   "large-v3-turbo"    -> RECOMMENDED on CPU: ~88-92% Urdu, ~3-8 s for 10 s clip on i7 (~1.5 GB)
#   "large-v3"          -> best quality but slow on CPU (~3 GB, ~15-50 s on i7)
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "large-v3-turbo")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")  # "cpu" | "cuda"
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")  # "int8" (CPU) | "float16" (GPU)

# Maximum upload size (bytes) for /api/transcribe. Default 25 MB.
TRANSCRIBE_MAX_BYTES = int(os.getenv("TRANSCRIBE_MAX_BYTES", str(25 * 1024 * 1024)))

# Inngest Settings
INNGEST_APP_ID = os.getenv("INNGEST_APP_ID", "GOTHAM")

# Cloudinary Settings
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
CLOUDINARY_FOLDER = os.getenv("CLOUDINARY_FOLDER", "gotham")
CLOUDINARY_PUBLIC_URLS = os.getenv("CLOUDINARY_PUBLIC_URLS", "true").lower() == "true"

# App Settings
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# JWT (required in production; dev falls back when DEBUG=true)
_JWT_FROM_ENV = os.getenv("JWT_SECRET", "").strip()
if _JWT_FROM_ENV:
    JWT_SECRET = _JWT_FROM_ENV
elif DEBUG:
    JWT_SECRET = "dev-insecure-jwt-secret-change-me"
else:
    # Test runner: keep import-time config from crashing collection.
    try:
        import sys

        _is_pytest = "pytest" in sys.modules
    except Exception:
        _is_pytest = False
    if _is_pytest:
        JWT_SECRET = "test-jwt-secret"
    else:
        raise ValueError(
            "JWT_SECRET environment variable must be set when DEBUG is false. "
            "Generate a long random string (e.g. openssl rand -hex 32)."
        )

JWT_ACCESS_MINUTES = int(os.getenv("JWT_ACCESS_MINUTES", "1440"))  # default 24h
JWT_REFRESH_DAYS = int(os.getenv("JWT_REFRESH_DAYS", "30"))

ALLOW_LEGACY_PASSWORD_HASH = os.getenv("ALLOW_LEGACY_PASSWORD_HASH", "true").lower() == "true"
ALLOW_LEGACY_HEADER_AUTH = os.getenv("ALLOW_LEGACY_HEADER_AUTH", "true").lower() == "true"

# CORS (comma-separated origins; empty = use localhost defaults in main.py)
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()

# Rate limiting (slowapi)
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    
    # Reduce verbose logging to prevent terminal overflow
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("inngest").setLevel(logging.WARNING)
