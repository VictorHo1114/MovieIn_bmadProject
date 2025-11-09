from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT title, keywords 
        FROM movies 
        WHERE keywords IS NOT NULL 
        AND jsonb_array_length(keywords) > 0 
        ORDER BY vote_count DESC 
        LIMIT 5
    """))
    
    print(" 前 5 部電影的 Keywords:\n")
    for row in result:
        print(f"【{row[0]}】")
        print(f"  {row[1][:10]}...\n" if len(row[1]) > 10 else f"  {row[1]}\n")
