"""Check if ALL new CTG fields were populated."""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def check_all_ctg_fields():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()
    
    # Check P007's data (should have complete CTG)
    cursor.execute("""
        SELECT 
            fetal_baseline_value, fetal_accelerations, fetal_movement,
            uterine_contractions, light_decelerations,
            histogram_width, histogram_mean, histogram_variance
        FROM patient_latest_assessments pla
        JOIN patients p ON p.id = pla.patient_id
        WHERE p.patient_identifier = 'P007'
    """)
    
    row = cursor.fetchone()
    if row:
        print("P007 CTG Data in Materialized Table:")
        print("="*60)
        print(f"  Baseline: {row[0]}")
        print(f"  Accelerations: {row[1]}")
        print(f"  Movement: {row[2]}")
        print(f"  Uterine Contractions: {row[3]}")
        print(f"  Light Decelerations: {row[4]}")
        print(f"  Histogram Width: {row[5]}")
        print(f"  Histogram Mean: {row[6]}")
        print(f"  Histogram Variance: {row[7]}")
        
        nulls = sum(1 for x in row if x is None)
        if nulls == 0:
            print("\n✅ ALL FIELDS POPULATED!")
        else:
            print(f"\n❌ {nulls} fields are NULL")
    else:
        print("P007 not found in materialized table")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_all_ctg_fields()
