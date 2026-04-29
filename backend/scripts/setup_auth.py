"""
Setup authentication system.

This script:
1. Creates the auth_users table
2. Seeds authentication users (doctor + patients)
3. Lists all created users

Run: python scripts/setup_auth.py
"""

from pathlib import Path
import sys

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.init_db import create_db_and_tables
from scripts.seed_auth_users import seed_auth_users


def main():
    print("=" * 60)
    print("🔐 GOTHAM Authentication Setup")
    print("=" * 60)
    
    print("\n📊 Step 1: Creating database tables...")
    try:
        create_db_and_tables()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return
    
    print("\n👥 Step 2: Seeding authentication users...")
    try:
        seed_auth_users()
        print("\n✅ Authentication setup complete!")
    except Exception as e:
        print(f"❌ Error seeding users: {e}")
        return
    
    print("\n" + "=" * 60)
    print("✅ AUTHENTICATION SYSTEM READY")
    print("=" * 60)
    print("\n📝 Login Credentials:")
    print("   Doctor: Dr. Ali Mahmud / 123")
    print("   Patients: [patient name] / 123")
    print("\n🌐 API Endpoints:")
    print("   POST /auth/login - Login endpoint")
    print("   GET  /auth/users - List all users")
    print("\n💡 Test the API at: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
