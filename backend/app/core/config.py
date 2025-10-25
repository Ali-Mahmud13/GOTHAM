"""Application configuration."""

import logging
import os
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

# Inngest Settings
INNGEST_APP_ID = os.getenv("INNGEST_APP_ID", "GOTHAM")

# App Settings
DEBUG = os.getenv("DEBUG", "false").lower() == "true"


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
