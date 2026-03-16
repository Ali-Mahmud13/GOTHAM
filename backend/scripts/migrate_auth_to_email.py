"""
Migrate auth_users table from username to email.

This script drops and recreates the auth_users table with the new email-based schema.

Run: python scripts/migrate_auth_to_email.py
"""

from pathlib import Path
import sys

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.db import engine


def migrate_auth_table():
    """Drop and recreate auth_users table with email field."""
    
    print("=" * 60)
    print("🔄 Migrating auth_users table to email-based authentication")
    print("=" * 60)
    
    with engine.connect() as conn:
        print("\n📊 Step 1: Dropping old auth_users table...")
        try:
            conn.execute(text("DROP TABLE IF EXISTS auth_users CASCADE"))
            conn.commit()
            print("✅ Old table dropped successfully")
        except Exception as e:
            print(f"❌ Error dropping table: {e}")
            return False
        
        print("\n📊 Step 2: Creating new auth_users table with email...")
        try:
            create_table_sql = """
            CREATE TABLE auth_users (
                id SERIAL PRIMARY KEY,
                email VARCHAR UNIQUE NOT NULL,
                password_hash VARCHAR NOT NULL,
                role VARCHAR NOT NULL,
                full_name VARCHAR,
                patient_id INTEGER REFERENCES patients(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            );
            
            CREATE INDEX idx_auth_users_email ON auth_users(email);
            """
            conn.execute(text(create_table_sql))
            conn.commit()
            print("✅ New table created successfully")
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("✅ Migration completed successfully!")
    print("=" * 60)
    print("\n💡 Next step: Run 'python scripts/seed_auth_users.py' to populate users")
    
    return True


if __name__ == "__main__":
    migrate_auth_table()
