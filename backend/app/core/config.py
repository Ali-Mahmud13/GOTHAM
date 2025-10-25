"""Application configuration."""

import logging
import os


# Settings
INNGEST_APP_ID = os.getenv("INNGEST_APP_ID", "GOTHAM")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
