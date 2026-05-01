"""Create partial unique index to prevent double-booking the same doctor slot."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg2


def _load_database_url() -> str:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.is_file():
        raise RuntimeError(f"Missing {env_path}")
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() == "DATABASE_URL":
            return v.strip().strip('"').strip("'")
    raise RuntimeError("DATABASE_URL not found in backend/.env")


def main() -> None:
    url = _load_database_url()
    conn = psycopg2.connect(url)
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_appt_active_slot
                  ON appointments (doctor_id, appointment_date, start_time)
                  WHERE status IN ('booked', 'pending_approval');
                """
            )
            conn.commit()
            print("OK: uq_appt_active_slot created (or already exists).")
        finally:
            cur.close()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
