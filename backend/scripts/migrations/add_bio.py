import sys
import os
from dotenv import load_dotenv

# Load .env from backend root
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(backend_dir, '.env'))

from sqlalchemy import text
from app.db.session import engine

def run():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE auth_users ADD COLUMN bio TEXT DEFAULT NULL"))
            conn.commit()
            print("[OK] Added bio column")
        except Exception as e:
            print(f"bio: {e}")

if __name__ == "__main__":
    run()
