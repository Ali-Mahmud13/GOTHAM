"""Quick script to verify database has patient data."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from app.db.session import engine
from app.models import Patient, Visit

def main():
    """Check database contents."""
    with Session(engine) as session:
        # Count patients
        patients = session.exec(select(Patient)).all()
        print(f"\n✓ Total patients in database: {len(patients)}")
        
        # Count visits
        visits = session.exec(select(Visit)).all()
        print(f"✓ Total visits in database: {len(visits)}")
        
        # Show sample patient IDs
        if patients:
            print(f"\nSample patient IDs:")
            for patient in patients[:5]:
                print(f"  - {patient.patient_identifier}")
        
        # Show latest visit dates
        if visits:
            print(f"\nLatest visits:")
            for visit in sorted(visits, key=lambda v: v.visit_date, reverse=True)[:3]:
                patient = session.get(Patient, visit.patient_id)
                print(f"  - Patient {patient.patient_identifier}: {visit.visit_date}")

if __name__ == "__main__":
    main()
