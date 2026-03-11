"""Main application."""

import inngest.fast_api
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import setup_logging
from app.inngest import inngest_client, ALL_FUNCTIONS
from app.api.chat import router as chat_router
from app.api.data_entry import router as data_entry_router
from app.api.patients import router as patients_router
from app.api.dashboard import router as dashboard_router
from app.api.patient_portal import router as patient_portal_router
from app.api.auth import router as auth_router
from app.api.appointments import router as appointments_router
from app.db.init_db import create_db_and_tables
from app.db.session import engine
from sqlalchemy import text

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
    # Add new columns to existing tables if they don't exist yet
    with engine.connect() as conn:
        for col_sql in [
            "ALTER TABLE appointments ADD COLUMN rescheduled_by TEXT",
            "ALTER TABLE appointments ADD COLUMN cancelled_by TEXT",
        ]:
            try:
                conn.execute(text(col_sql))
                conn.commit()
            except Exception:
                pass  # Column already exists

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Inngest
inngest.fast_api.serve(app, inngest_client, ALL_FUNCTIONS)

# Register API routes
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(data_entry_router)
app.include_router(patients_router)
app.include_router(dashboard_router)
app.include_router(patient_portal_router)
app.include_router(appointments_router)


@app.get("/")
async def root():
    return {"app": "GOTHAM", "docs": "/docs"}


@app. get("/health")
async def health():
    return {"status": "healthy"}