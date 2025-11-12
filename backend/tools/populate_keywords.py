"""
從 TMDB API 獲取電影關鍵詞並填充到資料庫
"""
import os
import time
import json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import requests

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

def get_movie_keywords(tmdb_id: int, max_retries=3):
    """從 TMDB API 獲取電影關鍵詞（支援重試）"""
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/keywords"
    params = {"api_key": TMDB_API_KEY}
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                keywords = [kw["name"] for kw in data.get("keywords", [])]
                return keywords
            return []
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"  ⏱️  Timeout, retry {attempt + 1}/{max_retries}...")
                time.sleep(2)
                continue
            return []
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return []
    return []

def update_movie_keywords():
    """批次更新電影關鍵詞（支援斷點續傳和連線重連）"""
    success_count = 0
    error_count = 0
    
    while True:
        try:
            with engine.connect() as conn:
                # 只獲取還沒有 keywords 的電影（斷點續傳）
                result = conn.execute(text("""
                    SELECT tmdb_id, title FROM movies 
                    WHERE keywords IS NULL OR jsonb_array_length(keywords) = 0
                    ORDER BY vote_count DESC
                """))
                movies = [(row[0], row[1]) for row in result]
                
                if not movies:
                    print("✨ 所有電影都已有 keywords！")
                    return
                
                print(f"🎬 開始更新 {len(movies)} 部電影的關鍵詞...")
                print("=" * 70)
                
                for i, (tmdb_id, title) in enumerate(movies):
                    try:
                        keywords = get_movie_keywords(tmdb_id)
                        
                        if keywords:
                            keywords_json = json.dumps(keywords)
                            conn.execute(
                                text("UPDATE movies SET keywords = :keywords WHERE tmdb_id = :tmdb_id"),
                                {"keywords": keywords_json, "tmdb_id": tmdb_id}
                            )
                            conn.commit()
                            success_count += 1
                            print(f"✅ [{i+1}/{len(movies)}] {title[:50]:<50} - {len(keywords)} keywords")
                        else:
                            conn.execute(
                                text("UPDATE movies SET keywords = '[]' WHERE tmdb_id = :tmdb_id"),
                                {"tmdb_id": tmdb_id}
                            )
                            conn.commit()
                            print(f"⚠️  [{i+1}/{len(movies)}] {title[:50]:<50} - No keywords")
                        
                        # 每 50 部顯示進度
                        if (i + 1) % 50 == 0:
                            print(f"\n📊 進度: {i+1}/{len(movies)} ({(i+1)/len(movies)*100:.1f}%) | 成功: {success_count} | 無資料: {error_count}\n")
                        
                        time.sleep(0.3)  # 加長間隔避免超時
                        
                    except KeyboardInterrupt:
                        print("\n\n⚠️  使用者中斷！")
                        print(f"已處理: {i}/{len(movies)} 部電影")
                        print("下次執行會從中斷處繼續（斷點續傳）")
                        return
                    except Exception as e:
                        error_count += 1
                        print(f"❌ [{i+1}/{len(movies)}] {title[:50]:<50} - Error: {e}")
                        time.sleep(3)
                        continue
                
                print("=" * 70)
                print(f"\n✨ 更新完成！")
                print(f"   成功: {success_count}")
                print(f"   錯誤: {error_count}")
                print(f"   剩餘: {len(movies) - success_count - error_count}")
                return
                
        except Exception as db_error:
            print(f"\n⚠️  資料庫連線中斷: {db_error}")
            print("🔄 5 秒後重新連線...")
            time.sleep(5)
            continue
    """批次更新電影關鍵詞 - 處理所有電影"""
    with engine.connect() as conn:
        # 獲取所有沒有 keywords 的電影（優先高評分）
        result = conn.execute(text("""
            SELECT tmdb_id, title 
            FROM movies 
            WHERE keywords IS NULL OR jsonb_array_length(keywords) = 0
            ORDER BY vote_count DESC
        """))
        movies = [(row[0], row[1]) for row in result]
        
        print(f"🎬 開始更新 {len(movies)} 部電影的關鍵詞...")
        print("=" * 70)
        
        success_count = 0
        error_count = 0
        
        for i, (tmdb_id, title) in enumerate(movies, 1):
            keywords = get_movie_keywords(tmdb_id)
            
            if keywords:
                # 轉換為 JSON 格式
                keywords_json = json.dumps(keywords)
                
                # 更新資料庫
                conn.execute(
                    text("UPDATE movies SET keywords = :keywords WHERE tmdb_id = :tmdb_id"),
                    {"keywords": keywords_json, "tmdb_id": tmdb_id}
                )
                conn.commit()  # 每次更新後立即提交
                success_count += 1
                print(f"✅ [{i}/{len(movies)}] {title[:40]:<40} - {len(keywords)} keywords")
            else:
                # 即使沒有 keywords 也更新為空陣列（標記已處理）
                conn.execute(
                    text("UPDATE movies SET keywords = '[]' WHERE tmdb_id = :tmdb_id"),
                    {"tmdb_id": tmdb_id}
                )
                conn.commit()
                error_count += 1
                print(f"⚠️  [{i}/{len(movies)}] {title[:40]:<40} - No keywords")
            
            # 每 50 部顯示進度
            if i % 50 == 0:
                print(f"\n📊 進度: {i}/{len(movies)} ({i/len(movies)*100:.1f}%) | 成功: {success_count} | 無資料: {error_count}\n")
            
            # 避免超過 API 限制（每秒 4 次）
            time.sleep(0.25)
        
        print("=" * 70)
        print(f"\n✨ 更新完成！")
        print(f"   成功: {success_count}/{len(movies)} 部電影")
        print(f"   無資料: {error_count}/{len(movies)} 部電影")

if __name__ == "__main__":
    update_movie_keywords()
