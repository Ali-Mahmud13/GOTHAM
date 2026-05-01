"""Create doctor_schedule_exceptions table for per-date schedule overrides."""

from __future__ import annotations

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
                CREATE TABLE IF NOT EXISTS doctor_schedule_exceptions (
                  id SERIAL PRIMARY KEY,
                  doctor_id INTEGER NOT NULL REFERENCES auth_users(id),
                  exception_date TEXT NOT NULL,
                  kind TEXT NOT NULL CHECK (kind IN ('blocked', 'custom')),
                  start_time TEXT NULL,
                  end_time TEXT NULL,
                  slot_duration_minutes INTEGER NULL,
                  timezone TEXT NOT NULL DEFAULT 'UTC',
                  notes TEXT NULL,
                  created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_dse_doctor_date
                  ON doctor_schedule_exceptions (doctor_id, exception_date);
                """
            )
            cur.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_dse_blocked
                  ON doctor_schedule_exceptions (doctor_id, exception_date)
                  WHERE kind = 'blocked';
                """
            )
            conn.commit()
            print("OK: doctor_schedule_exceptions table + indexes ready.")
        finally:
            cur.close()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
