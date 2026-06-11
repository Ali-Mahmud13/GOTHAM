"""
Migration: Add doctor verification and credential fields to auth_users table.

Run with: python backend/scripts/migrations/add_doctor_verification_fields.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from sqlalchemy import text
from app.db.session import engine


def run():
    with engine.connect() as conn:
        # Add verification_status column (nullable, default NULL)
        try:
            conn.execute(text(
                "ALTER TABLE auth_users ADD COLUMN verification_status VARCHAR(32) DEFAULT NULL"
            ))
            print("[OK] Added verification_status column")
        except Exception as e:
            print(f"  verification_status: {e}")

        # Add license_number
        try:
            conn.execute(text(
                "ALTER TABLE auth_users ADD COLUMN license_number VARCHAR(128) DEFAULT NULL"
            ))
            print("[OK] Added license_number column")
        except Exception as e:
            print(f"  license_number: {e}")

        # Add specialty
        try:
            conn.execute(text(
                "ALTER TABLE auth_users ADD COLUMN specialty VARCHAR(128) DEFAULT NULL"
            ))
            print("[OK] Added specialty column")
        except Exception as e:
            print(f"  specialty: {e}")

        # Add clinic_name
        try:
            conn.execute(text(
                "ALTER TABLE auth_users ADD COLUMN clinic_name VARCHAR(256) DEFAULT NULL"
            ))
            print("[OK] Added clinic_name column")
        except Exception as e:
            print(f"  clinic_name: {e}")

        # Backfill: existing doctors who were already active get 'verified' status
        # so they continue to appear in the patient booking flow.
        conn.execute(text(
            """
            UPDATE auth_users
            SET verification_status = 'verified'
            WHERE role = 'doctor'
              AND is_active = true
              AND verification_status IS NULL
            """
        ))
        print("[OK] Backfilled existing active doctors as 'verified'")

        conn.commit()
        print("\nMigration complete.")


if __name__ == "__main__":
    run()
