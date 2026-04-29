"""Main application."""

# Disable TensorFlow/Keras imports in transformers before any other imports
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TF logs
os.environ['TRANSFORMERS_OFFLINE'] = '0'

import inngest.fast_api
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
from sqlalchemy import inspect

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
    # Ensure schema drift is healed on startup for existing deployments.
    try:
        inspector = inspect(engine)
        existing_columns = {
            c["name"] for c in inspector.get_columns("appointments")
        }
        required_columns = {
            "rescheduled_by": "TEXT",
            "cancelled_by": "TEXT",
        }

        with engine.connect() as conn:
            for col_name, col_type in required_columns.items():
                if col_name not in existing_columns:
                    logger.warning(
                        "Missing appointments.%s column detected. Applying startup migration...",
                        col_name,
                    )
                    conn.execute(text(f"ALTER TABLE appointments ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    logger.info("✓ Added appointments.%s", col_name)

        visit_columns = {c["name"] for c in inspector.get_columns("visits")}
        required_visit_columns = {
            "recorded_by_role": "TEXT",
            "recorded_by_user_id": "INTEGER",
        }
        with engine.connect() as conn:
            for col_name, col_type in required_visit_columns.items():
                if col_name not in visit_columns:
                    logger.warning(
                        "Missing visits.%s column detected. Applying startup migration...",
                        col_name,
                    )
                    conn.execute(text(f"ALTER TABLE visits ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    logger.info("✓ Added visits.%s", col_name)
    except Exception as e:
        logger.error(
            "Failed while ensuring appointments migration columns: %s",
            str(e),
            exc_info=True,
        )

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

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def ensure_local_cors_headers(request: Request, call_next):
    """Force CORS headers for localhost origins, even on error paths."""
    response = await call_next(request)
    origin = request.headers.get("origin", "")
    if origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1"):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
    return response

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