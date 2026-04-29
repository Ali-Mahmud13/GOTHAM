"""Check P007's CBC data in materialized table."""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

cursor.execute("""
    SELECT 
        p.patient_identifier,
        pla.wbc, pla.rbc, pla.hgb, pla.hct,
        pla.mcv, pla.mch, pla.mchc, pla.plt
    FROM patient_latest_assessments pla
    JOIN patients p ON p.id = pla.patient_id
    WHERE p.patient_identifier = 'P007'
""")

row = cursor.fetchone()
if row:
    print(f"P007 CBC Data in Materialized Table:")
    print(f"  WBC: {row[1]}")
    print(f"  RBC: {row[2]}")
    print(f"  HGB: {row[3]}")
    print(f"  HCT: {row[4]}")
    print(f"  MCV: {row[5]}")
    print(f"  MCH: {row[6]}")
    print(f"  MCHC: {row[7]}")
    print(f"  PLT: {row[8]}")
    
    nulls = sum(1 for x in row[1:] if x is None)
    print(f"\n{'✅ ALL CBC FIELDS POPULATED' if nulls == 0 else f'❌ {nulls} fields are NULL'}")
else:
    print("P007 not found")

cursor.close()
conn.close()
