import sys
import os
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(backend_dir, '.env'))

from sqlalchemy import text
from app.db.session import engine

def run():
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS maternal_health_assessments (
                    id SERIAL PRIMARY KEY,
                    visit_id INTEGER NOT NULL REFERENCES visits(id),
                    body_temp FLOAT DEFAULT NULL,
                    heart_rate INTEGER DEFAULT NULL,
                    risk_level INTEGER DEFAULT NULL,
                    confidence FLOAT DEFAULT NULL,
                    ai_report TEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_maternal_health_visit_id ON maternal_health_assessments(visit_id)"
            ))
            conn.commit()
            print("[OK] Created maternal_health_assessments table")
        except Exception as e:
            print(f"maternal_health_assessments: {e}")

if __name__ == "__main__":
    run()
