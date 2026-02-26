"""Add missing fetal health fields to materialized table."""

import os
from dotenv import load_dotenv
import psycopg2
from pathlib import Path

load_dotenv()

def add_fetal_fields():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()
    
    sql_file = Path(__file__).parent / "add_fetal_fields.sql"
    with open(sql_file, 'r') as f:
        sql = f.read()
    
    print("Adding missing fetal health fields to patient_latest_assessments...")
    
    try:
        cursor.execute(sql)
        conn.commit()
        print("✓ All fetal health fields added successfully!")
        
        # Verify
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns
            WHERE table_name = 'patient_latest_assessments'
              AND column_name LIKE 'fetal%' OR column_name LIKE '%histogram%'
                OR column_name LIKE '%deceleration%' OR column_name LIKE '%variability%'
                OR column_name = 'uterine_contractions'
        """)
        
        count = cursor.fetchone()[0]
        print(f"Total fetal-related columns: {count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_fetal_fields()
