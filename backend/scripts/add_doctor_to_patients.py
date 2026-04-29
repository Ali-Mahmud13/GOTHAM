"""Migration script to add doctor_id to patients table and assign all existing patients to Dr. Ali Mahmud."""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, create_engine, text, select
from app.core.config import DATABASE_URL
from app.models.patient import Patient
from app.models.auth import AuthUser


def migrate_add_doctor_to_patients():
    """Add doctor_id column and assign all patients to Dr. Ali Mahmud."""
    
    engine = create_engine(DATABASE_URL)
    
    with Session(engine) as session:
        try:
            # Step 1: Add doctor_id column if it doesn't exist
            print("Adding doctor_id column to patients table...")
            session.exec(text("""
                ALTER TABLE patients 
                ADD COLUMN IF NOT EXISTS doctor_id INTEGER;
            """))
            session.commit()
            print("✅ Column added successfully")
            
            # Step 2: Add foreign key constraint
            print("Adding foreign key constraint...")
            try:
                session.exec(text("""
                    ALTER TABLE patients 
                    ADD CONSTRAINT fk_patients_doctor 
                    FOREIGN KEY (doctor_id) REFERENCES auth_users(id) ON DELETE SET NULL;
                """))
                session.commit()
                print("✅ Foreign key constraint added")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("⚠️  Foreign key constraint already exists")
                    session.rollback()
                else:
                    raise
            
            # Step 3: Add index on doctor_id
            print("Adding index on doctor_id...")
            try:
                session.exec(text("""
                    CREATE INDEX IF NOT EXISTS ix_patients_doctor_id ON patients(doctor_id);
                """))
                session.commit()
                print("✅ Index created")
            except Exception as e:
                print(f"⚠️  Index creation: {e}")
                session.rollback()
            
            # Step 4: Get Dr. Ali Mahmud's ID
            print("\nFinding Dr. Ali Mahmud...")
            dr_ali = session.exec(
                select(AuthUser).where(AuthUser.email == "dralimahmud@gotham.com")
            ).first()
            
            if not dr_ali:
                print("❌ Dr. Ali Mahmud not found in auth_users table!")
                print("Please run seed_auth_users.py first.")
                return
            
            print(f"✅ Found Dr. Ali Mahmud (ID: {dr_ali.id})")
            
            # Step 5: Assign all existing patients to Dr. Ali
            print(f"\nAssigning all patients to Dr. Ali Mahmud (ID: {dr_ali.id})...")
            result = session.exec(text(f"""
                UPDATE patients 
                SET doctor_id = {dr_ali.id} 
                WHERE doctor_id IS NULL;
            """))
            session.commit()
            
            # Count total patients
            total_patients = session.exec(
                select(Patient).where(Patient.doctor_id == dr_ali.id)
            ).all()
            
            print(f"✅ Assigned {len(total_patients)} patients to Dr. Ali Mahmud")
            
            # Display patient list
            print("\nPatients assigned to Dr. Ali Mahmud:")
            for patient in total_patients:
                print(f"  - {patient.patient_identifier}: {patient.name}")
            
            print("\n✅ Migration completed successfully!")
            print(f"All {len(total_patients)} existing patients are now assigned to Dr. Ali Mahmud")
            print("New doctors will start with an empty patient list.")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            session.rollback()
            raise


if __name__ == "__main__":
    migrate_add_doctor_to_patients()
