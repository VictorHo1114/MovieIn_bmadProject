import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine, text

engine = create_engine(os.getenv("DATABASE_URL"))

print("\n" + "="*80)
print(" Embedding 語言匹配診斷")
print("="*80 + "\n")

with engine.connect() as conn:
    # 1. 檢查電影 overview 語言分佈
    print("【1】電影 Overview 語言分析 (隨機 10 部)\n")
    result = conn.execute(text("""
        SELECT title, overview 
        FROM movies 
        ORDER BY RANDOM()
        LIMIT 10
    """))
    
    chinese_count = 0
    english_count = 0
    
    for row in result:
        title, overview = row[0], row[1]
        if not overview:
            continue
        has_chinese = any(0x4e00 <= ord(c) <= 0x9fff for c in overview[:200])
        lang = "中文" if has_chinese else "英文"
        
        if has_chinese:
            chinese_count += 1
        else:
            english_count += 1
        
        print(f"  {lang:4} | {title[:50]}")
        print(f"       | {overview[:80]}...")
        print()
    
    print(f"統計: 中文 {chinese_count} 部, 英文 {english_count} 部\n")
    print("-" * 80 + "\n")
    
    # 2. 檢查 movie_vectors 表的內容
    print("【2】Movie Vectors 表統計\n")
    result = conn.execute(text("""
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as with_embedding
        FROM movie_vectors
    """))
    row = result.first()
    if row:
        print(f"  總記錄數: {row[0]}")
        print(f"  有 Embedding: {row[1]}")
    
    print("\n" + "="*80)
    print(" 診斷完成")
    print("="*80 + "\n")