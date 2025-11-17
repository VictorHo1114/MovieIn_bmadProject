import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("錯誤: 未設置 DATABASE_URL")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

# 要刪除的電影 tmdb_id
problematic_ids = [1025527, 1305717, 861451, 1373276, 1096563, 1511789]

with engine.begin() as conn:
    # 刪除前先顯示這些電影
    print("\n  準備刪除以下電影:")
    for tmdb_id in problematic_ids:
        result = conn.execute(text(
            "SELECT title, LENGTH(overview) as overview_len, vote_count FROM movies WHERE tmdb_id = :id"
        ), {"id": tmdb_id}).fetchone()
        if result:
            print(f"   - {result[0]} (tmdb_id: {tmdb_id}, 簡介長度: {result[1]}, 評分數: {result[2]})")
    
    # 執行刪除
    print("\n  執行刪除...")
    result = conn.execute(text(
        "DELETE FROM movies WHERE tmdb_id = ANY(:ids)"
    ), {"ids": problematic_ids})
    
    deleted_count = result.rowcount
    print(f" 已刪除 {deleted_count} 部電影")
    
    # 顯示最終統計
    total = conn.execute(text("SELECT COUNT(*) FROM movies")).scalar()
    qualified = conn.execute(text("""
        SELECT COUNT(*) FROM movies
        WHERE title IS NOT NULL AND title != ''
          AND overview IS NOT NULL AND overview != ''
          AND LENGTH(overview) >= 20
          AND genres IS NOT NULL AND genres::text != '[]'
          AND poster_path IS NOT NULL AND poster_path != ''
          AND vote_count >= 5
    """)).scalar()
    
    print(f"\n 刪除後統計:")
    print(f"   - 總電影數: {total}")
    print(f"   - 完全合格: {qualified} ({qualified*100/total:.1f}%)")
    
    # 驗證沒有問題的電影了
    remaining_problems = conn.execute(text("""
        SELECT COUNT(*) FROM movies
        WHERE overview IS NULL OR overview = '' 
           OR LENGTH(overview) < 20
           OR vote_count < 5
    """)).scalar()
    
    if remaining_problems == 0:
        print(f"    所有電影資料完整！")
    else:
        print(f"     仍有 {remaining_problems} 部電影有問題")
