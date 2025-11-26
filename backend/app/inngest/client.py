"""Inngest client."""

import logging
import os
import inngest
from app.core.config import INNGEST_APP_ID

# Create Inngest client
# For local dev, point to the dev server at localhost:8288
# The dev server accepts any fake event key
event_key = os.getenv("INNGEST_EVENT_KEY", "local-dev-key")
event_api_base_url = os.getenv("INNGEST_EVENT_API_BASE_URL", "http://localhost:8288")

inngest_client = inngest.Inngest(
    app_id=INNGEST_APP_ID,
    event_key=event_key,
    event_api_base_url=event_api_base_url,  # Point to local dev server
    logger=logging.getLogger("uvicorn"),
)
