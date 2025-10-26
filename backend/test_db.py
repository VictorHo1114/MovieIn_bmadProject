import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    now = conn.execute(text("SELECT now()")).scalar_one()
    print("DB OK. now() =", now)