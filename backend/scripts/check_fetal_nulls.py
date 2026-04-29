"""Check which fetal health fields are NULL in materialized table."""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def check_fetal_nulls():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()
    
    # Get all fetal-related columns
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns
        WHERE table_name = 'patient_latest_assessments'
          AND column_name LIKE 'fetal%'
        ORDER BY column_name
    """)
    
    fetal_columns = [row[0] for row in cursor.fetchall()]
    print(f"Fetal columns in materialized table: {len(fetal_columns)}")
    print("\nColumns:", fetal_columns)
    
    # Check which columns have NULLs for patients with fetal data
    print("\n" + "="*60)
    print("Checking NULL values for patients with fetal assessments:")
    print("="*60)
    
    for col in fetal_columns:
        if col.endswith('_updated_at'):
            continue
            
        cursor.execute(f"""
            SELECT p.patient_identifier, pla.{col}
            FROM patient_latest_assessments pla
            JOIN patients p ON p.id = pla.patient_id
            WHERE pla.fetal_baseline_value IS NOT NULL
        """)
        
        results = cursor.fetchall()
        nulls = [r for r in results if r[1] is None]
        
        if nulls:
            print(f"\n❌ {col}: {len(nulls)} patients with NULL")
            for patient_id, _ in nulls:
                print(f"   - {patient_id}")
        else:
            print(f"✓ {col}: All populated")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_fetal_nulls()
