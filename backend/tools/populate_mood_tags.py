"""
填充 mood_tags - 批次處理版本
"""
import os
import json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from openai import OpenAI
import time

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MOOD_TAGS_REFERENCE = [
    # 情緒類
    "hopeful", "inspiring", "emotional", "uplifting", "heartwarming",
    "intense", "dark", "thrilling", "suspenseful", "thought-provoking",
    "funny", "lighthearted", "whimsical", "cheerful", "feel-good",
    "romantic", "passionate", "bittersweet", "melancholic",
    "epic", "grand", "adventurous", "exciting", "action-packed",
    "terrifying", "creepy", "disturbing", "mysterious",
    # 氛圍類
    "cozy", "relaxing", "comforting", "gritty", "realistic",
    "atmospheric", "moody", "dreamy", "fast-paced", "contemplative",
    # 主題類
    "mind-bending", "philosophical", "heartbreaking", "empowering",
    "escapist", "fantastical", "magical", "imaginative",
]

def analyze_batch(movies_batch):
    """批次分析多部電影"""
    results = []
    
    for movie in movies_batch:
        tmdb_id, title, overview, genres, keywords = movie
        
        # 簡化 prompt
        prompt = f"""電影: {title}
類型: {", ".join(genres[:3]) if genres else "unknown"}
關鍵詞: {", ".join(keywords[:5]) if keywords else "none"}

從以下標籤中選 5 個最適合的（逗號分隔）:
{", ".join(MOOD_TAGS_REFERENCE[:30])}

只返回標籤，如: intense, dark, thrilling, epic, atmospheric"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=50
            )
            
            tags_text = response.choices[0].message.content.strip()
            tags = [tag.strip() for tag in tags_text.split(",")]
            valid_tags = [tag for tag in tags if tag in MOOD_TAGS_REFERENCE][:5]
            
            results.append((tmdb_id, title, valid_tags))
            
        except Exception as e:
            print(f"    {title}: {str(e)[:50]}")
            results.append((tmdb_id, title, []))
        
        time.sleep(0.5)  # 避免 rate limit
    
    return results

with engine.connect() as conn:
    # 只處理前 20 部（測試）
    result = conn.execute(text("""
        SELECT tmdb_id, title, overview, genres, keywords
        FROM movies
        WHERE keywords IS NOT NULL 
        AND (mood_tags IS NULL OR mood_tags = \'[]\'::jsonb)
        ORDER BY popularity DESC
        LIMIT 20
    """))
    
    movies = result.fetchall()
    print(f" 處理 {len(movies)} 部電影...")
    
    # 批次處理（每 5 部一批）
    for i in range(0, len(movies), 5):
        batch = movies[i:i+5]
        print(f"\n--- Batch {i//5 + 1} ---")
        
        results = analyze_batch(batch)
        
        # 更新到資料庫
        for tmdb_id, title, mood_tags in results:
            if mood_tags:
                conn.execute(
                    text("""
                        UPDATE movies 
                        SET mood_tags = :mood_tags
                        WHERE tmdb_id = :tmdb_id
                    """),
                    {
                        "mood_tags": json.dumps(mood_tags),
                        "tmdb_id": tmdb_id
                    }
                )
                print(f"   {title}: {mood_tags}")
        
        conn.commit()
    
    print(f"\n 完成！")
