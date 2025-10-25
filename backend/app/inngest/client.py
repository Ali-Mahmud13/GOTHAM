"""Inngest client."""

import logging
import inngest
from app.core.config import INNGEST_APP_ID

# Create Inngest client (just like Next.js: new Inngest({ id: "..." }))
inngest_client = inngest.Inngest(
    app_id=INNGEST_APP_ID,
    logger=logging.getLogger("uvicorn"),
)
