"""
批次填充缺失的 Embeddings（只處理熱門電影前 500 部）
"""
import os, json, time
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text as sql_text
from openai import OpenAI

engine = create_engine(os.getenv("DATABASE_URL"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_embedding(content: str) -> list:
    """生成文本的 embedding"""
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=content
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"     Embedding 生成失敗: {e}")
        return None

print(f"\n{'='*70}")
print(f" 開始補齊熱門電影 Embeddings")
print(f"{'='*70}\n")

with engine.connect() as conn:
    # 找出熱門電影（前 500）中缺少 embedding 的電影
    result = conn.execute(sql_text("""
        SELECT m.tmdb_id, m.title, m.overview
        FROM movies m
        WHERE m.tmdb_id IN (
            SELECT tmdb_id FROM movies ORDER BY popularity DESC LIMIT 500
        )
        AND m.tmdb_id NOT IN (
            SELECT tmdb_id FROM movie_vectors
        )
        ORDER BY m.popularity DESC
    """))
    
    missing_movies = result.fetchall()
    total = len(missing_movies)
    
    if total == 0:
        print(" 所有熱門電影已有 embeddings！")
        print(f"\n{'='*70}\n")
        exit(0)
    
    print(f" 找到 {total} 部缺少 embedding 的熱門電影")
    print(f"  預估時間: {total * 0.5:.1f} 秒\n")
    
    success = 0
    failed = 0
    
    for idx, (tmdb_id, title, overview) in enumerate(missing_movies, 1):
        print(f"[{idx}/{total}] {title[:40]}...", end=" ")
        
        # 構建文本（標題 + 簡介）
        movie_text = f"{title}. {overview or ''}"
        
        # 生成 embedding
        embedding = generate_embedding(movie_text)
        
        if embedding:
            # 存入資料庫
            conn.execute(sql_text("""
                INSERT INTO movie_vectors (tmdb_id, embedding)
                VALUES (:tmdb_id, :embedding)
            """), {
                "tmdb_id": tmdb_id,
                "embedding": json.dumps(embedding)
            })
            conn.commit()
            success += 1
            print(f"")
        else:
            failed += 1
            print(f"")
        
        # Rate limit
        time.sleep(0.3)
        
        # 每 10 部顯示進度
        if idx % 10 == 0:
            print(f"\n 進度: {idx}/{total} ({idx/total*100:.1f}%) | 成功: {success} | 失敗: {failed}\n")

print(f"\n{'='*70}")
print(f" 補齊完成！")
print(f"{'='*70}")
print(f"   成功: {success} 部")
print(f"   失敗: {failed} 部")
print(f"   成功率: {success/total*100:.1f}%")
print(f"\n{'='*70}\n")
