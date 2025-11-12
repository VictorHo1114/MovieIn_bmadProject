#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys
from pathlib import Path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
from dotenv import load_dotenv
load_dotenv(dotenv_path=backend_dir / ".env")
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.services.embedding_service import store_movie_embedding
engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(bind=engine)
def main():
    print("="*60)
    print(" 開始為數據庫電影預計算 embeddings")
    print("="*60)
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT tmdb_id, title, overview FROM movies ORDER BY vote_average DESC"))
        movies = result.fetchall()
        total = len(movies)
        print(f"\n 數據庫共有 {total} 部電影")
        existing = db.execute(text("SELECT COUNT(DISTINCT tmdb_id) FROM movie_vectors")).scalar()
        print(f" 已有 {existing} 部電影的 embeddings")
        print(f" 需要計算 {total - existing} 部\n")
        success = skip = errors = 0
        for i, m in enumerate(movies, 1):
            if not m.overview or len(m.overview.strip()) < 20:
                skip += 1
                continue
            try:
                store_movie_embedding(db, m.tmdb_id, m.overview)
                success += 1
                if success <= 20 or success % 50 == 0:
                    print(f"   [{i}/{total}] {m.title}")
                if i % 100 == 0:
                    print(f"\n 進度：{i}/{total} | 成功:{success} | 跳過:{skip} | 失敗:{errors}\n")
            except Exception as e:
                errors += 1
                if errors <= 10:
                    print(f"   失敗: {m.title[:30]} - {str(e)[:40]}")
        print(f"\n{'='*60}\n 完成！總計:{total} | 成功:{success} | 跳過:{skip} | 失敗:{errors}\n 空間: ~{success*6.4/1024:.2f} MB |  成本: ~${success*0.00001:.4f}\n{'='*60}")
    finally:
        db.close()
if __name__ == "__main__":
    main()
