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

def get_movie_keywords(tmdb_id: int):
    """從 TMDB API 獲取電影關鍵詞"""
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/keywords"
    params = {"api_key": TMDB_API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            keywords = [kw["name"] for kw in data.get("keywords", [])]
            return keywords
        return []
    except Exception as e:
        print(f"Error fetching keywords for {tmdb_id}: {e}")
        return []

def update_movie_keywords():
    """批次更新電影關鍵詞"""
    with engine.connect() as conn:
        # 獲取所有電影 ID（優先高評分電影）
        result = conn.execute(text("SELECT tmdb_id, title FROM movies ORDER BY vote_count DESC LIMIT 100"))
        movies = [(row[0], row[1]) for row in result]
        
        print(f"開始更新 {len(movies)} 部電影的關鍵詞...")
        print("=" * 70)
        
        success_count = 0
        for i, (tmdb_id, title) in enumerate(movies):
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
                print(f"✅ [{i+1}/{len(movies)}] {title[:30]:<30} - {len(keywords)} keywords")
            else:
                print(f"⚠️  [{i+1}/{len(movies)}] {title[:30]:<30} - No keywords")
            
            # 避免超過 API 限制（每秒 4 次）
            time.sleep(0.25)
        
        print("=" * 70)
        print(f"\n✨ 更新完成！成功: {success_count}/{len(movies)} 部電影")

if __name__ == "__main__":
    update_movie_keywords()
