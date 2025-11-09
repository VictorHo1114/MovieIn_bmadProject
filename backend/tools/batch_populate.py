"""
批次填充 Keywords + Mood Tags - 優化版
處理前 500 部熱門電影
"""
import os, json, time
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from openai import OpenAI
import requests

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

MOOD_TAGS_REF = [
    "hopeful", "inspiring", "emotional", "uplifting", "heartwarming",
    "intense", "dark", "thrilling", "suspenseful", "thought-provoking",
    "funny", "lighthearted", "cheerful", "feel-good", "whimsical",
    "romantic", "passionate", "bittersweet", "melancholic",
    "epic", "grand", "adventurous", "exciting", "action-packed",
    "terrifying", "creepy", "disturbing", "mysterious", "eerie",
    "cozy", "relaxing", "comforting", "gritty", "realistic",
    "atmospheric", "moody", "dreamy", "fast-paced", "contemplative",
    "mind-bending", "philosophical", "heartbreaking", "empowering",
    "escapist", "fantastical", "magical", "imaginative",
]

def fetch_keywords_from_tmdb(tmdb_id: int) -> list:
    """從 TMDB 獲取 keywords"""
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/keywords"
        response = requests.get(url, params={"api_key": TMDB_API_KEY}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [kw["name"] for kw in data.get("keywords", [])[:20]]
        return []
    except:
        return []

def analyze_mood_tags(title: str, genres: list, keywords: list) -> list:
    """使用 GPT 分析 mood tags"""
    prompt = f"""電影: {title}
類型: {", ".join(genres[:3])}
關鍵詞: {", ".join(keywords[:5])}

從以下標籤選 5 個最適合的（逗號分隔）:
{", ".join(MOOD_TAGS_REF[:25])}

只返回標籤: intense, dark, thrilling, epic, atmospheric"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=50
        )
        tags = [t.strip() for t in response.choices[0].message.content.split(",")]
        return [t for t in tags if t in MOOD_TAGS_REF][:5]
    except:
        # 備援：根據 genre 返回預設值
        defaults = {
            "动作": ["intense", "exciting", "action-packed"],
            "剧情": ["emotional", "thought-provoking"],
            "喜剧": ["funny", "lighthearted", "cheerful"],
        }
        result = []
        for g in genres[:2]:
            result.extend(defaults.get(g, [])[:2])
        return list(set(result))[:3]

print(" 開始批次處理...")
print("=" * 70)

with engine.connect() as conn:
    # 取得前 500 部熱門電影
    result = conn.execute(text("""
        SELECT tmdb_id, title, genres
        FROM movies
        ORDER BY popularity DESC
        LIMIT 500
    """))
    movies = result.fetchall()
    
    print(f" 處理 {len(movies)} 部電影\n")
    
    success_kw = 0
    success_mt = 0
    
    # 每 20 部一批
    for i in range(0, len(movies), 20):
        batch = movies[i:i+20]
        batch_num = i // 20 + 1
        
        print(f"\n--- Batch {batch_num}/{(len(movies)-1)//20 + 1} ---")
        
        for tmdb_id, title, genres in batch:
            # 檢查是否已有資料
            check = conn.execute(text("""
                SELECT keywords, mood_tags 
                FROM movies 
                WHERE tmdb_id = :id
            """), {"id": tmdb_id}).fetchone()
            
            has_kw = check[0] and check[0] != []
            has_mt = check[1] and check[1] != []
            
            # 更新 keywords
            if not has_kw:
                keywords = fetch_keywords_from_tmdb(tmdb_id)
                if keywords:
                    conn.execute(text("""
                        UPDATE movies 
                        SET keywords = :kw
                        WHERE tmdb_id = :id
                    """), {"kw": json.dumps(keywords), "id": tmdb_id})
                    success_kw += 1
                    print(f"   KW: {title[:30]}")
                time.sleep(0.3)  # Rate limit
            
            # 更新 mood_tags
            if not has_mt:
                # 取得 keywords（剛更新的或原有的）
                kw_data = keywords if not has_kw else (check[0] or [])
                mood_tags = analyze_mood_tags(title, genres or [], kw_data)
                
                if mood_tags:
                    conn.execute(text("""
                        UPDATE movies 
                        SET mood_tags = :mt
                        WHERE tmdb_id = :id
                    """), {"mt": json.dumps(mood_tags), "id": tmdb_id})
                    success_mt += 1
                    print(f"   MT: {title[:30]}")
                time.sleep(0.5)  # GPT rate limit
        
        conn.commit()
        print(f" Batch {batch_num} 完成 (KW: {success_kw}, MT: {success_mt})")

print(f"\n{'=' * 70}")
print(f" 完成！")
print(f"  - Keywords: {success_kw} 部")
print(f"  - Mood Tags: {success_mt} 部")
