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

def analyze_movie(tmdb_id, title, overview, genres, keywords, max_retries=3):
    """分析單部電影並返回 mood_tags"""
    # 提取 genre 名稱
    genre_names = []
    if genres:
        for g in genres:
            if isinstance(g, dict):
                genre_names.append(g.get('name', ''))
            else:
                genre_names.append(str(g))
    
    # 簡化 prompt
    prompt = f"""電影: {title}
類型: {", ".join(genre_names[:3]) if genre_names else "unknown"}
關鍵詞: {", ".join(keywords[:5]) if keywords else "none"}

從以下標籤中選 5 個最適合的（逗號分隔）:
{", ".join(MOOD_TAGS_REFERENCE)}

只返回標籤，如: intense, dark, thrilling, epic, atmospheric"""

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=50
            )
            
            tags_text = response.choices[0].message.content.strip()
            tags = [tag.strip().lower() for tag in tags_text.split(",")]
            valid_tags = [tag for tag in tags if tag in MOOD_TAGS_REFERENCE][:5]
            
            return valid_tags if valid_tags else ["emotional", "engaging"]
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  ⏱️  Retry {attempt + 1}/{max_retries}...")
                time.sleep(2)
                continue
            print(f"  ❌ Error: {str(e)[:50]}")
            return ["emotional", "engaging"]  # 預設值
    
    return ["emotional", "engaging"]

def update_mood_tags():
    """更新所有電影的 mood_tags（支援斷點續傳）"""
    success_count = 0
    error_count = 0
    
    while True:
        try:
            with engine.connect() as conn:
                # 只獲取還沒有 mood_tags 的電影（斷點續傳）
                result = conn.execute(text("""
                    SELECT tmdb_id, title, overview, genres, keywords
                    FROM movies
                    WHERE keywords IS NOT NULL 
                    AND jsonb_array_length(keywords) > 0
                    AND (mood_tags IS NULL OR jsonb_array_length(mood_tags) = 0)
                    ORDER BY popularity DESC
                """))
                
                movies = result.fetchall()
                total = len(movies)
                
                if total == 0:
                    print("✨ 所有電影都已有 mood_tags！")
                    return
                
                print(f"🎬 開始處理 {total} 部電影的 mood_tags...")
                print("=" * 70)
                
                for i, movie in enumerate(movies, 1):
                    tmdb_id, title, overview, genres, keywords = movie
                    
                    try:
                        mood_tags = analyze_movie(tmdb_id, title, overview, genres, keywords)
                        
                        # 更新到資料庫
                        conn.execute(
                            text("UPDATE movies SET mood_tags = :mood_tags WHERE tmdb_id = :tmdb_id"),
                            {"mood_tags": json.dumps(mood_tags), "tmdb_id": tmdb_id}
                        )
                        conn.commit()
                        success_count += 1
                        print(f"✅ [{i}/{total}] {title[:45]:<45} - {mood_tags}")
                        
                    except KeyboardInterrupt:
                        print("\n\n⚠️  使用者中斷！")
                        print(f"已處理: {i-1}/{total} 部電影")
                        print("下次執行會從中斷處繼續（斷點續傳）")
                        return
                    except Exception as e:
                        error_count += 1
                        print(f"❌ [{i}/{total}] {title[:45]:<45} - Error: {str(e)[:30]}")
                        # 設定預設值
                        conn.execute(
                            text("UPDATE movies SET mood_tags = :mood_tags WHERE tmdb_id = :tmdb_id"),
                            {"mood_tags": json.dumps(["emotional", "engaging"]), "tmdb_id": tmdb_id}
                        )
                        conn.commit()
                        time.sleep(2)
                        continue
                    
                    # 每 50 部顯示進度
                    if i % 50 == 0:
                        print(f"\n📊 進度: {i}/{total} ({i/total*100:.1f}%) | 成功: {success_count} | 錯誤: {error_count}\n")
                    
                    time.sleep(0.5)  # 避免 rate limit
                
                print("=" * 70)
                print(f"\n✨ 更新完成！")
                print(f"   成功: {success_count}")
                print(f"   錯誤: {error_count}")
                return
                
        except Exception as db_error:
            print(f"\n⚠️  資料庫連線中斷: {db_error}")
            print("🔄 5 秒後重新連線...")
            time.sleep(5)
            continue

if __name__ == "__main__":
    update_mood_tags()
