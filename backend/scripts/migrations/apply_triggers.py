"""
Apply PostgreSQL triggers for patient_latest_assessments.

This script connects to your Neon database and runs the trigger SQL.

Run with: python scripts/migrations/apply_triggers.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

def apply_triggers():
    """Apply triggers to the database."""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not found in .env")
        return False
    
    print("Connecting to database...")
    
    # Read SQL file
    sql_file = Path(__file__).parent / "create_latest_assessments_triggers.sql"
    with open(sql_file, 'r') as f:
        sql = f.read()
    
    try:
        # Connect and execute
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("Applying triggers...")
        cursor.execute(sql)
        conn.commit()
        
        print("✓ Triggers created successfully!")
        print("\nVerifying triggers...")
        
        # Verify
        cursor.execute("""
            SELECT trigger_name, event_object_table
            FROM information_schema.triggers
            WHERE trigger_schema = 'public'
              AND trigger_name IN ('gdm_update_latest', 'anemia_update_latest', 'fetal_update_latest')
        """)
        
        triggers = cursor.fetchall()
        for trigger_name, table_name in triggers:
            print(f"  ✓ {trigger_name} on {table_name}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error applying triggers: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = apply_triggers()
    sys.exit(0 if success else 1)
