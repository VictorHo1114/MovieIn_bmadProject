import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

CREATE_SQL = """
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    username VARCHAR UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now()
);
"""

def main():
    # Load env variables from backend/.env if present
    load_dotenv()
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    engine = create_engine(url)
    with engine.begin() as conn:
        # 檢查現有結構
        cols = conn.execute(text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
            """
        )).fetchall()
        colnames = [c[0] for c in cols]
        
        # 需要重建的條件：表不存在、缺少 id 欄位、或缺少 username 欄位
        needs_recreate = (len(colnames) == 0) or ("id" not in colnames) or ("username" not in colnames)
        
        if needs_recreate:
            print(f"Current columns: {colnames}")
            print("Recreating users table with correct schema...")
            conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            conn.execute(text(CREATE_SQL))
            print("✓ Recreated users table.")
        else:
            print("users table looks OK:", colnames)

if __name__ == "__main__":
    main()
