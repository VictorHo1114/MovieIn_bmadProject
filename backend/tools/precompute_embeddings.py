#!/usr/bin/env python3
"""
為數據庫中所有電影預先計算 embeddings
"""
import os
import sys
from pathlib import Path

# 加入專案路徑
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv

# 明確載入 backend/.env
env_path = backend_dir / ".env"
load_dotenv(dotenv_path=env_path)

print(f"[DEBUG] .env path: {env_path}")
print(f"[DEBUG] OPENAI_API_KEY exists: {bool(os.getenv('OPENAI_API_KEY'))}")
print(f"[DEBUG] DATABASE_URL exists: {bool(os.getenv('DATABASE_URL'))}")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.services.embedding_service import store_movie_embedding

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


async def fetch_popular_movies(page: int = 1) -> list:
    """從 TMDB 取得熱門電影"""
    async with httpx.AsyncClient() as client:
        url = "https://api.themoviedb.org/3/movie/popular"
        params = {
            "api_key": TMDB_API_KEY,
            "language": "zh-TW",
            "page": page
        }
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])


async def main():
    """主函數：預計算前 500 部熱門電影"""
    print("="*60)
    print("🎬 開始預計算電影 embeddings（目標：500 部）")
    print("="*60)
    
    db = SessionLocal()
    total_processed = 0
    target_count = 500
    max_pages = 100  # 最多處理 100 頁，確保達到 500 部有效電影
    
    try:
        for page in range(1, max_pages + 1):
            if total_processed >= target_count:
                print(f"\n🎯 已達成目標！共 {total_processed} 部電影")
                break
                
            print(f"\n📄 正在處理第 {page}/{max_pages} 頁...")
            
            try:
                movies = await fetch_popular_movies(page)
                
                for i, movie in enumerate(movies, 1):
                    if total_processed >= target_count:
                        break
                        
                    tmdb_id = movie.get("id")
                    title = movie.get("title", "Unknown")
                    overview = movie.get("overview", "")
                    
                    if not overview or len(overview.strip()) < 20:
                        print(f"  ⏭️  跳過 {title} (無簡介)")
                        continue
                    
                    try:
                        store_movie_embedding(db, tmdb_id, overview)
                        total_processed += 1
                        print(f"  ✓ [{total_processed}] {title} (ID: {tmdb_id})")
                        
                        # 每 100 部顯示進度
                        if total_processed % 100 == 0:
                            print(f"\n📊 進度：已處理 {total_processed} / {target_count} 部電影\n")
                        
                    except Exception as e:
                        print(f"  ✗ 失敗: {title} - {e}")
                
                # 避免 TMDB API 限流（每秒最多 40 次請求）
                await asyncio.sleep(0.3)
                
            except Exception as e:
                print(f"  ❌ 頁面 {page} 處理失敗: {e}")
                continue
        
        print("\n" + "="*60)
        print(f"✅ 完成！共處理 {total_processed} 部電影")
        print(f"� 資料庫儲存空間：~{total_processed * 6.4 / 1024:.2f} MB")
        print(f"�💰 預估成本：~${total_processed * 0.000003:.4f} USD")
        print("="*60)
        
    finally:
        db.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())