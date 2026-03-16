"""
Create patient_latest_assessments table.

Run with: python scripts/migrations/create_latest_table.py
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import engine
from app.models.patient_latest_assessments import PatientLatestAssessments
from sqlmodel import SQLModel

def create_latest_assessments_table():
    """Create the patient_latest_assessments table."""
    print("Creating patient_latest_assessments table...")
    
    # Create only this specific table
    PatientLatestAssessments.metadata.create_all(engine)
    
    print("✓ Table created successfully!")
    print("\nNext step: Run the trigger script:")
    print("  psql <your_database_url> -f scripts/migrations/create_latest_assessments_triggers.sql")

if __name__ == "__main__":
    create_latest_assessments_table()
