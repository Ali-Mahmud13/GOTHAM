"""Check fetal health assessment table structure."""

import os
from dotenv import load_dotenv  
import psycopg2

load_dotenv()

def check_fetal_schema():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()
    
    # Get all columns from fetal_health_assessments
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'fetal_health_assessments'
        ORDER BY ordinal_position
    """)
    
    print("Fetal Health Assessment Table Columns:")
    print("="*60)
    columns = cursor.fetchall()
    for col, dtype in columns:
        print(f"  {col}: {dtype}")
    
    print(f"\nTotal: {len(columns)} columns")
    
    # Check sample data
    cursor.execute("""
        SELECT 
            baseline_value, accelerations, fetal_movement,
            uterine_contractions, light_decelerations,
            histogram_width, histogram_mean
        FROM fetal_health_assessments
        LIMIT 2
    """)
    
    print("\nSample CTG Data:")
    print("="*60)
    for row in cursor.fetchall():
        print(f"  Baseline: {row[0]}, Accelerations: {row[1]}, Movement: {row[2]}")
        print(f"  Contractions: {row[3]}, Light Decel: {row[4]}")
        print(f"  Histogram Width: {row[5]}, Mean: {row[6]}")
        print()
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_fetal_schema()
