import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def main():
    load_dotenv()
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    engine = create_engine(url)
    with engine.connect() as conn:
        print("Connected to:", url)
        res = conn.execute(text(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
            """
        ))
        cols = res.fetchall()
        print("users columns:")
        for c in cols:
            print(" -", c[0], c[1])

if __name__ == "__main__":
    main()
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


def main():
    load_dotenv()
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL not set")
    engine = create_engine(url)
    with engine.connect() as conn:
        print("DB:", url.split("@")[1][:40] + "...")
        res = conn.execute(text(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
            """
        ))
        cols = res.fetchall()
        print("users columns (name, type, nullable):")
        for c in cols:
            print(" -", c)

        # preview rows
        res2 = conn.execute(text("SELECT * FROM users LIMIT 1"))
        row = res2.fetchone()
        print("one row:", dict(row) if row else None)


if __name__ == "__main__":
    main()
