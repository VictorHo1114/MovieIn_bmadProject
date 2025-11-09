from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # 添加新欄位
    conn.execute(text("ALTER TABLE movies ADD COLUMN IF NOT EXISTS keywords JSONB DEFAULT '[]'::jsonb"))
    conn.execute(text("ALTER TABLE movies ADD COLUMN IF NOT EXISTS mood_tags JSONB DEFAULT '[]'::jsonb"))
    conn.execute(text("ALTER TABLE movies ADD COLUMN IF NOT EXISTS tone TEXT"))
    
    # 創建索引
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_movies_keywords ON movies USING GIN (keywords)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_movies_mood_tags ON movies USING GIN (mood_tags)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_movies_tone ON movies(tone)"))
    
    conn.commit()
    print(" Successfully added keywords, mood_tags, and tone columns")
