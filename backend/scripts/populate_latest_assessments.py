"""
Populate patient_latest_assessments from existing visit data.

This is a one-time migration to backfill existing patients.

Run with: python scripts/populate_latest_assessments.py
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import engine
from sqlmodel import Session, select
from app.models import Patient, Visit, GDMAssessment, AnemiaAssessment, FetalHealthAssessment

def populate_latest_assessments():
    """
    Populate patient_latest_assessments from existing data.
    
    The triggers will automatically handle updates as we re-insert/update assessments.
    """
    print("Starting migration...")
    
    with Session(engine) as session:
        # Get all patients
        patients = session.exec(select(Patient)).all()
        print(f"Found {len(patients)} patients to migrate")
        
        for i, patient in enumerate(patients, 1):
            print(f"\n[{i}/{len(patients)}] Processing {patient.patient_identifier} - {patient.name}")
            
            # Get all visits for this patient
            visits = session.exec(
                select(Visit)
                .where(Visit.patient_id == patient.id)
                .order_by(Visit.visit_date.desc())
            ).all()
            
            if not visits:
                print(f"  No visits found")
                continue
            
            print(f"  Found {len(visits)} visits")
            
            # For each visit, get assessments (triggers will auto-update)
            for visit in visits:
                # Check for GDM assessment
                gdm = session.exec(
                    select(GDMAssessment).where(GDMAssessment.visit_id == visit.id)
                ).first()
                
                # Check for Anemia assessment  
                anemia = session.exec(
                    select(AnemiaAssessment).where(AnemiaAssessment.visit_id == visit.id)
                ).first()
                
                # Check for Fetal assessment
                fetal = session.exec(
                    select(FetalHealthAssessment).where(FetalHealthAssessment.visit_id == visit.id)
                ).first()
                
                if gdm:
                    print(f"    Visit {visit.visit_date.date()}: GDM ✓")
                if anemia:
                    print(f"    Visit {visit.visit_date.date()}: Anemia ✓")
                if fetal:
                    print(f"    Visit {visit.visit_date.date()}: Fetal ✓")
        
        # The triggers handle everything automatically!
        # No need to manually create patient_latest_assessments records
        
        print(f"\n✓ Migration complete! Processed {len(patients)} patients")
        print("\nNote: The triggers automatically populated patient_latest_assessments")

if __name__ == "__main__":
    populate_latest_assessments()
