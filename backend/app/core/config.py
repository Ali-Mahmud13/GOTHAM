"""Application configuration."""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database Settings
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
