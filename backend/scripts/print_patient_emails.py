from __future__ import annotations

def _load_database_url() -> str:
    with open("backend/.env", "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == "DATABASE_URL":
                return v.strip().strip('"').strip("'")
    raise RuntimeError("DATABASE_URL missing in backend/.env")


def main() -> None:
    import psycopg2

    url = _load_database_url()
    conn = psycopg2.connect(url)
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                "select email from auth_users "
                "where role='patient' and email is not null "
                "order by id asc limit 20"
            )
            rows = cur.fetchall()
            for (email,) in rows:
                print(email)
        finally:
            cur.close()
    finally:
        conn.close()


if __name__ == "__main__":
    main()

