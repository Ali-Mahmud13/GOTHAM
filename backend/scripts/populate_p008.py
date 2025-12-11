"""Quick script to populate patient_latest_assessments for P008"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

# SQL to populate for P008
sql = """
INSERT INTO patient_latest_assessments (
    patient_id,
    latest_gdm_visit_id,
    gdm_risk_level,
    gdm_confidence,
    latest_anemia_visit_id,
    anemia_diagnosis,
    anemia_confidence,
    latest_fetal_visit_id,
    fetal_health_status,
    fetal_health_confidence,
    last_updated
)
SELECT 
    p.id as patient_id,
    NULL as latest_gdm_visit_id,
    NULL as gdm_risk_level,
    NULL as gdm_confidence,
    v.id as latest_anemia_visit_id,
    aa.diagnosis as anemia_diagnosis,
    aa.confidence as anemia_confidence,
    NULL as latest_fetal_visit_id,
    NULL as fetal_health_status,
    NULL as fetal_health_confidence,
    NOW() as last_updated
FROM patients p
JOIN visits v ON v.patient_id = p.id
JOIN anemia_assessments aa ON aa.visit_id = v.id
WHERE p.patient_identifier = 'P008'
  AND NOT EXISTS (
    SELECT 1 FROM patient_latest_assessments pla WHERE pla.patient_id = p.id
  )
ORDER BY v.visit_date DESC
LIMIT 1;
"""

try:
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        conn.commit()
        print(f"✅ Inserted {result.rowcount} row(s) into patient_latest_assessments for P008")
except Exception as e:
    print(f"❌ Error: {e}")
