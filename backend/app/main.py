"""Main application."""

# Disable TensorFlow/Keras imports in transformers before any other imports
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TF logs
os.environ['TRANSFORMERS_OFFLINE'] = '0'

import inngest
import inngest.fast_api
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
from sqlalchemy import inspect

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.rate_limit import limiter
from app.core.config import setup_logging
from app.core import config
from app.inngest import inngest_client, ALL_FUNCTIONS
from app.api.chat import router as chat_router
from app.api.data_entry import router as data_entry_router
from app.api.patients import router as patients_router
from app.api.dashboard import router as dashboard_router
from app.api.patient_portal import router as patient_portal_router
from app.api.auth import router as auth_router
from app.api.appointments import router as appointments_router
from app.api.transcription import router as transcription_router
from app.db.init_db import create_db_and_tables
from app.db.session import engine
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Setup
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("Initializing database tables...")
    try:
        create_db_and_tables()
        logger.info("✓ Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)

    # Data hygiene: unregistered patients should not retain doctor-authored notes.
    try:
        with engine.connect() as conn:
            patient_update = conn.execute(
                text(
                    """
                    UPDATE patients
                    SET clinical_notes = NULL
                    WHERE doctor_id IS NULL AND clinical_notes IS NOT NULL
                    """
                )
            )
            visit_update = conn.execute(
                text(
                    """
                    UPDATE visits
                    SET notes = NULL
                    WHERE patient_id IN (SELECT id FROM patients WHERE doctor_id IS NULL)
                      AND COALESCE(visit_type, '') <> 'clinical_notes'
                      AND notes IS NOT NULL
                    """
                )
            )
            conn.commit()

            if patient_update.rowcount or visit_update.rowcount:
                logger.info(
                    "Applied unregistered-notes cleanup: patients=%s, visits=%s",
                    patient_update.rowcount,
                    visit_update.rowcount,
                )
    except Exception as e:
        logger.error(
            "Failed while cleaning unregistered patient notes: %s",
            str(e),
            exc_info=True,
        )

    yield
    # Shutdown logic goes here if needed


app = FastAPI(title="GOTHAM - Medical Agent System", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Removed legacy on_event startup logic

# CORS for React frontend
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
]
if config.CORS_ALLOWED_ORIGINS:
    origins.extend([o.strip() for o in config.CORS_ALLOWED_ORIGINS.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Inngest — streaming sends keepalive bytes so long-running
# step handlers (ML inference, LLM calls) don't hit idle-connection resets.
if "pytest" not in sys.modules:
    inngest.fast_api.serve(
        app,
        inngest_client,
        ALL_FUNCTIONS,
        streaming=inngest.Streaming.FORCE,
    )

# Register API routes
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(data_entry_router)
app.include_router(patients_router)
app.include_router(dashboard_router)
app.include_router(patient_portal_router)
app.include_router(appointments_router)
app.include_router(transcription_router)


@app.get("/")
async def root():
    return {"app": "GOTHAM", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "healthy"}