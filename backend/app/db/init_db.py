"""Database initialization and setup utilities."""

from sqlmodel import SQLModel
from app.db.session import engine
from app.models import Patient, Visit, User, AuthUser
import logging

logger = logging.getLogger(__name__)


def create_db_and_tables():
    """
    Create all database tables.
    
    This should be called on application startup or via a migration script.
    """
    logger.info("Creating database tables...")
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created successfully")


def drop_db_and_tables():
    """
    Drop all database tables.
    
    WARNING: This will delete all data! Use only in development.
    """
    logger.warning("Dropping all database tables...")
    SQLModel.metadata.drop_all(engine)
    logger.info("Database tables dropped")


def reset_db():
    """
    Drop and recreate all database tables.
    
    WARNING: This will delete all data! Use only in development.
    """
    drop_db_and_tables()
    create_db_and_tables()
