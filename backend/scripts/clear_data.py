"""Clear existing patient and visit data to re-run migration."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session
from app.db.session import engine
from app.models import Patient, Visit
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clear_data():
    """Delete all patient and visit data."""
    with Session(engine) as session:
        # Delete all visits first (foreign key constraint)
        visits = session.query(Visit).all()
        for visit in visits:
            session.delete(visit)
        logger.info(f"Deleted {len(visits)} visits")
        
        # Delete all patients
        patients = session.query(Patient).all()
        for patient in patients:
            session.delete(patient)
        logger.info(f"Deleted {len(patients)} patients")
        
        session.commit()
        logger.info("✓ All data cleared successfully!")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Clearing existing patient and visit data...")
    logger.info("=" * 60)
    clear_data()
    logger.info("\nNow run: python scripts/migrate_csv_to_db.py")
