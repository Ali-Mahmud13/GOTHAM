"""Check what data P007 actually has in the database."""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def check_p007():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()
    
    # Check if P007 exists
    cursor.execute("SELECT id, patient_identifier, name FROM patients WHERE patient_identifier = 'P007'")
    patient = cursor.fetchone()
    
    if not patient:
        print("❌ P007 does not exist in database")
        cursor.close()
        conn.close()
        return
    
    patient_id = patient[0]
    print(f"✓ Found: {patient[2]} (ID: {patient_id})")
    
    # Check visits
    cursor.execute("SELECT COUNT(*) FROM visits WHERE patient_id = %s", (patient_id,))
    visit_count = cursor.fetchone()[0]
    print(f"  Visits: {visit_count}")
    
    # Check GDM assessments
    cursor.execute("""
        SELECT COUNT(*) FROM gdm_assessments ga
        JOIN visits v ON v.id = ga.visit_id
        WHERE v.patient_id = %s
    """, (patient_id,))
    gdm_count = cursor.fetchone()[0]
    print(f"  GDM assessments: {gdm_count}")
    
    # Check Anemia assessments
    cursor.execute("""
        SELECT COUNT(*) FROM anemia_assessments aa
        JOIN visits v ON v.id = aa.visit_id
        WHERE v.patient_id = %s
    """, (patient_id,))
    anemia_count = cursor.fetchone()[0]
    print(f"  Anemia assessments: {anemia_count}")
    
    # Check Fetal assessments
    cursor.execute("""
        SELECT COUNT(*) FROM fetal_health_assessments fha
        JOIN visits v ON v.id = fha.visit_id
        WHERE v.patient_id = %s
    """, (patient_id,))
    fetal_count = cursor.fetchone()[0]
    print(f"  Fetal assessments: {fetal_count}")
    
    # Check materialized table
    print("\nMaterialized table data:")
    cursor.execute("""
        SELECT 
            glucose_level, sys_bp, bmi,
            wbc, hgb,
            fetal_baseline_value
        FROM patient_latest_assessments
        WHERE patient_id = %s
    """, (patient_id,))
    
    latest = cursor.fetchone()
    if latest:
        print(f"  Glucose: {latest[0]}")
        print(f"  Sys BP: {latest[1]}")
        print(f"  BMI: {latest[2]}")
        print(f"  WBC: {latest[3]}")
        print(f"  HGB: {latest[4]}")
        print(f"  Fetal Baseline: {latest[5]}")
    else:
        print("  No data in materialized table")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_p007()
