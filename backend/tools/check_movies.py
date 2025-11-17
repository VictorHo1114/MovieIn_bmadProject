import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import json

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("錯誤: 未設置 DATABASE_URL")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # 1. 檢查總數
    total = conn.execute(text("SELECT COUNT(*) FROM movies")).scalar()
    print(f"\n 資料庫電影總數: {total}")
    
    # 2. 檢查 tmdb_id 重複
    duplicates = conn.execute(text("""
        SELECT tmdb_id, COUNT(*) as count
        FROM movies
        GROUP BY tmdb_id
        HAVING COUNT(*) > 1
    """)).fetchall()
    
    if duplicates:
        print(f"\n 發現 {len(duplicates)} 個重複的 tmdb_id:")
        for dup in duplicates[:10]:
            print(f"   - tmdb_id: {dup[0]}, 重複次數: {dup[1]}")
    else:
        print(f"\n 無重複的 tmdb_id")
    
    # 3. 檢查必要欄位的完整性
    print(f"\n 資料完整性檢查:")
    
    # 檢查 title
    missing_title = conn.execute(text(
        "SELECT COUNT(*) FROM movies WHERE title IS NULL OR title = ''"
    )).scalar()
    print(f"   - 缺少標題 (title): {missing_title} 部")
    
    # 檢查 overview
    missing_overview = conn.execute(text(
        "SELECT COUNT(*) FROM movies WHERE overview IS NULL OR overview = ''"
    )).scalar()
    print(f"   - 缺少簡介 (overview): {missing_overview} 部")
    
    # 檢查簡介太短
    short_overview = conn.execute(text(
        "SELECT COUNT(*) FROM movies WHERE LENGTH(overview) < 20"
    )).scalar()
    print(f"   - 簡介太短 (<20字): {short_overview} 部")
    
    # 檢查 genres
    missing_genres = conn.execute(text(
        "SELECT COUNT(*) FROM movies WHERE genres IS NULL OR genres::text = '[]'"
    )).scalar()
    print(f"   - 缺少類型 (genres): {missing_genres} 部")
    
    # 檢查 poster_path
    missing_poster = conn.execute(text(
        "SELECT COUNT(*) FROM movies WHERE poster_path IS NULL OR poster_path = ''"
    )).scalar()
    print(f"   - 缺少海報 (poster_path): {missing_poster} 部")
    
    # 檢查評分數太少
    low_votes = conn.execute(text(
        "SELECT COUNT(*) FROM movies WHERE vote_count < 5"
    )).scalar()
    print(f"   - 評分數太少 (<5): {low_votes} 部")
    
    # 4. 顯示一些有問題的電影範例
    print(f"\n 有問題的電影範例 (前10部):")
    problematic = conn.execute(text("""
        SELECT tmdb_id, title, 
               LENGTH(overview) as overview_len,
               genres::text as genres,
               poster_path,
               vote_count
        FROM movies
        WHERE overview IS NULL OR overview = '' 
           OR LENGTH(overview) < 20
           OR genres IS NULL OR genres::text = '[]'
           OR poster_path IS NULL OR poster_path = ''
           OR vote_count < 5
        LIMIT 10
    """)).fetchall()
    
    if problematic:
        for movie in problematic:
            print(f"\n   tmdb_id: {movie[0]}")
            print(f"   標題: {movie[1]}")
            print(f"   簡介長度: {movie[2]}")
            print(f"   類型: {movie[3]}")
            print(f"   海報: {movie[4] or '無'}")
            print(f"   評分數: {movie[5]}")
    else:
        print("    沒有找到有問題的電影")
    
    # 5. 統計完全合格的電影
    qualified = conn.execute(text("""
        SELECT COUNT(*) FROM movies
        WHERE title IS NOT NULL AND title != ''
          AND overview IS NOT NULL AND overview != ''
          AND LENGTH(overview) >= 20
          AND genres IS NOT NULL AND genres::text != '[]'
          AND poster_path IS NOT NULL AND poster_path != ''
          AND vote_count >= 5
    """)).scalar()
    print(f"\n 完全合格的電影: {qualified} / {total} ({qualified*100/total:.1f}%)")
