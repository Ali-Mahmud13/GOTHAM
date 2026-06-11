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
    email = "dralimahmud@gotham.com"
    with engine.connect() as conn:
        result = conn.execute(
            text("UPDATE auth_users SET is_admin = true WHERE email = :email"),
            {"email": email}
        )
        conn.commit()
        if result.rowcount > 0:
            print(f"[SUCCESS] Made {email} an admin. Rows updated: {result.rowcount}")
        else:
            print(f"[WARNING] Could not find user {email} in the database.")

if __name__ == "__main__":
    run()
