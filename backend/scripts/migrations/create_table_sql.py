"""
Create patient_latest_assessments table via SQL.
"""

import os
from dotenv import load_dotenv
import psycopg2
from pathlib import Path

load_dotenv()

def create_table():
    """Create the table using SQL DDL."""
    database_url = os.getenv("DATABASE_URL")
    
    print("Connecting to database...")
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    try:
        # Read SQL file
        sql_file = Path(__file__).parent / "create_patient_latest_assessments_table.sql"
        with open(sql_file, 'r') as f:
            sql = f.read()
        
        print("Creating patient_latest_assessments table...")
        cursor.execute(sql)
        conn.commit()
        
        print("✓ Table created successfully!")
        
        # Verify
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns
            WHERE table_name = 'patient_latest_assessments'
            ORDER BY ordinal_position
            LIMIT 10
        """)
        
        print("\nSample columns:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]}")
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns
            WHERE table_name = 'patient_latest_assessments'
        """)
        col_count = cursor.fetchone()[0]
        print(f"\nTotal columns: {col_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_table()
