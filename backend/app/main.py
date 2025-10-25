"""Main application."""

import inngest.fast_api
from fastapi import FastAPI

from app.core.config import setup_logging
from app.inngest import inngest_client, ALL_FUNCTIONS

# Setup
setup_logging()
app = FastAPI(title="GOTHAM")

# Register Inngest
inngest.fast_api.serve(app, inngest_client, ALL_FUNCTIONS)


@app.get("/")
async def root():
    return {"app": "GOTHAM", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
