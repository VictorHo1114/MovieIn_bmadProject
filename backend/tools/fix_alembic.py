from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.begin() as conn:
    conn.execute(text("UPDATE alembic_version SET version_num = '342292faab66'"))
    print("✓ Updated alembic_version to 342292faab66")