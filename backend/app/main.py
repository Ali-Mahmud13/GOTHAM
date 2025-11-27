"""Main application."""

import inngest.fast_api
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import setup_logging
from app.inngest import inngest_client, ALL_FUNCTIONS
from app.api.chat import router as chat_router
from app.api.data_entry import router as data_entry_router
from app.db.init_db import create_db_and_tables

logger = logging.getLogger(__name__)

# Setup
setup_logging()
app = FastAPI(title="GOTHAM - Medical Agent System")

# Database initialization on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup."""
    logger.info("Initializing database tables...")
    try:
        create_db_and_tables()
        logger.info("✓ Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js default
        "http://localhost:5173",  # Vite default
        "http://localhost:8080",  # Current Vite config
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Inngest
inngest.fast_api.serve(app, inngest_client, ALL_FUNCTIONS)

# Register API routes
app.include_router(chat_router)
app.include_router(data_entry_router)




@app.get("/")
async def root():
    return {"app": "GOTHAM", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

