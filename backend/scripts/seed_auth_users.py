"""
Seed authentication users for GOTHAM system.

Creates:
- 1 Doctor: Dr. Ali Mahmud (dralimahmud@gotham.com)
- All existing patients as users with email format: firstname.lastname@gmail.com

Run: python scripts/seed_auth_users.py
"""

from sqlmodel import Session, select
from pathlib import Path
import sys
import hashlib
import re

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db import engine
from app.models import Patient, AuthUser


def hash_password(password: str) -> str:
    """Simple SHA256 hash for password. For production, use bcrypt/passlib."""
    return hashlib.sha256(password.encode()).hexdigest()


def name_to_email(name: str) -> str:
    """Convert full name to email format: firstname.lastname@gmail.com"""
    # Remove special characters and split by space
    name_clean = re.sub(r'[^a-zA-Z\s]', '', name).lower()
    parts = name_clean.split()
    
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}@gmail.com"
    else:
        return f"{parts[0]}@gmail.com"


def seed_auth_users():
    """Create authentication users for doctor and all patients."""
    
    with Session(engine) as session:
        print("🔐 Seeding Authentication Users...")
        
        # Clear existing auth users
        existing_users = session.exec(select(AuthUser)).all()
        for user in existing_users:
            session.delete(user)
        session.commit()
        print("  🗑️  Cleared existing auth users")
        
        # Create doctor account
        doctor = AuthUser(
            email="dralimahmud@gotham.com",
            full_name="Dr. Ali Mahmud",
            password_hash=hash_password("123"),
            role="doctor",
            patient_id=None,
            is_active=True
        )
        session.add(doctor)
        print("\n👨‍⚕️  Created Doctor Account:")
        print(f"    Email: dralimahmud@gotham.com")
        print(f"    Name: Dr. Ali Mahmud")
        print(f"    Password: 123")
        print(f"    Role: doctor")
        
        # Get all existing patients
        patients = session.exec(select(Patient)).all()
        
        if not patients:
            print("\n⚠️  No patients found in database. Please run seed_refactored_schema.py first.")
            session.commit()
            return
        
        print(f"\n👥 Creating Patient Accounts ({len(patients)} patients):")
        
        # Create patient accounts
        for patient in patients:
            email = name_to_email(patient.name)
            patient_user = AuthUser(
                email=email,
                full_name=patient.name,
                password_hash=hash_password("123"),
                role="patient",
                patient_id=patient.id,
                is_active=True
            )
            session.add(patient_user)
            print(f"    ✓ {patient.name} ({patient.patient_identifier}) - {email}")
        
        session.commit()
        
        print(f"\n✅ Successfully created {len(patients) + 1} auth users:")
        print(f"    - 1 doctor")
        print(f"    - {len(patients)} patients")
        print(f"\n📝 All passwords are set to: 123")
        print(f"\n📧 Email Format:")
        print(f"    Doctor: dralimahmud@gotham.com")
        print(f"    Patients: firstname.lastname@gmail.com")


if __name__ == "__main__":
    seed_auth_users()
