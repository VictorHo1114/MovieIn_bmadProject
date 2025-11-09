import os
import sys
import json
import time
import httpx
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 加載環境變數
load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

if not TMDB_API_KEY or not DATABASE_URL:
    print(" 請設置 TMDB_API_KEY 和 DATABASE_URL")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

def fetch_movies(endpoint, params, page=1):
    """通用的 TMDB API 調用"""
    url = f"https://api.themoviedb.org/3/{endpoint}"
    params.update({
        "api_key": TMDB_API_KEY,
        "language": "zh-TW",
        "page": page
    })
    response = httpx.get(url, params=params, timeout=10.0)
    response.raise_for_status()
    return response.json()

def fetch_popular_movies(page=1):
    """從 TMDB 獲取熱門電影"""
    return fetch_movies("movie/popular", {}, page)

def fetch_movie_details(tmdb_id):
    """獲取電影詳細資訊"""
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "zh-TW"
    }
    
    response = httpx.get(url, params=params, timeout=10.0)
    response.raise_for_status()
    return response.json()

def is_valid_movie(movie_data):
    """檢查電影資料是否齊全，適合推薦系統使用"""
    # 必須有標題
    if not movie_data.get("title"):
        return False, "缺少標題"
    
    # 必須有簡介（用於 embedding）
    overview = movie_data.get("overview", "").strip()
    if not overview or len(overview) < 20:
        return False, "簡介太短或缺失"
    
    # 必須有類型（用於分類過濾）
    genres = movie_data.get("genres", [])
    if not genres or len(genres) == 0:
        return False, "缺少類型"
    
    # 建議有海報（用於前端顯示）
    if not movie_data.get("poster_path"):
        return False, "缺少海報"
    
    # 建議有評分數據
    vote_count = movie_data.get("vote_count", 0)
    if vote_count < 5:  # 至少 5 個評分
        return False, f"評分數太少({vote_count})"
    
    return True, "符合標準"

def store_movie(conn, movie_data):
    """儲存電影到數據庫"""
    # 提取 genres（TMDB 返回的是對象陣列）
    genres = [g["name"] for g in movie_data.get("genres", [])]
    genres_json = json.dumps(genres, ensure_ascii=False)
    
    query = text("""
        INSERT INTO movies (
            tmdb_id, title, original_title, overview, 
            poster_path, backdrop_path, release_date, 
            genres, vote_average, vote_count, 
            popularity, runtime, original_language, adult
        ) VALUES (
            :tmdb_id, :title, :original_title, :overview,
            :poster_path, :backdrop_path, :release_date,
            CAST(:genres AS jsonb), :vote_average, :vote_count,
            :popularity, :runtime, :original_language, :adult
        )
        ON CONFLICT (tmdb_id) 
        DO UPDATE SET
            title = EXCLUDED.title,
            overview = EXCLUDED.overview,
            genres = EXCLUDED.genres,
            vote_average = EXCLUDED.vote_average,
            vote_count = EXCLUDED.vote_count,
            popularity = EXCLUDED.popularity,
            updated_at = now()
    """)
    
    conn.execute(query, {
        "tmdb_id": movie_data["id"],
        "title": movie_data.get("title", ""),
        "original_title": movie_data.get("original_title", ""),
        "overview": movie_data.get("overview", ""),
        "poster_path": movie_data.get("poster_path"),
        "backdrop_path": movie_data.get("backdrop_path"),
        "release_date": movie_data.get("release_date") or None,
        "genres": genres_json,
        "vote_average": float(movie_data.get("vote_average", 0.0)),
        "vote_count": int(movie_data.get("vote_count", 0)),
        "popularity": float(movie_data.get("popularity", 0.0)),
        "runtime": movie_data.get("runtime"),
        "original_language": movie_data.get("original_language", ""),
        "adult": bool(movie_data.get("adult", False))
    })

def import_from_source(conn, source_name, endpoint, params, pages, skip_count):
    """從指定來源導入電影"""
    print(f"\n{'='*60}")
    print(f"📚 來源: {source_name}")
    print(f"📄 頁數: {pages} 頁")
    print(f"{'='*60}\n")
    
    success = 0
    skipped = 0
    errors = 0
    
    for page in range(1, pages + 1):
        try:
            data = fetch_movies(endpoint, params, page)
            movies = data.get("results", [])
            
            for movie in movies:
                try:
                    details = fetch_movie_details(movie["id"])
                    
                    # 檢查資料完整性
                    is_valid, reason = is_valid_movie(details)
                    if not is_valid:
                        skipped += 1
                        if skipped + skip_count <= 10:  # 只顯示前10個
                            print(f"  ⏭️  跳過: {details.get('title', 'Unknown')[:30]} ({reason})")
                        continue
                    
                    store_movie(conn, details)
                    success += 1
                    print(f"  ✅ [{success}] {details['title'][:40]} - {source_name}")
                    time.sleep(0.3)
                    
                except Exception as e:
                    errors += 1
                    print(f"  ❌ 失敗: {movie.get('title', 'Unknown')}")
            
            if page % 3 == 0:
                count_result = conn.execute(text("SELECT COUNT(*) FROM movies"))
                print(f"\n  📊 目前總計: {count_result.scalar()} 部電影\n")
                
        except Exception as e:
            print(f"❌ 第 {page} 頁失敗: {e}")
    
    return success, skipped, errors

def main():
    print("🎬 開始多來源電影數據導入...")
    print("📊 策略: Popular + Top Rated + 各類型精選")
    print("🎯 目標: ~1000 部高品質電影")
    print("✅ 品質檢查: 簡介、類型、海報、評分\n")
    
    total_success = 0
    total_skipped = 0
    total_errors = 0
    
    with engine.begin() as conn:
        # 1. Popular - 前 500 名熱門電影（預計通過率 40-50%）
        s, sk, e = import_from_source(
            conn, "熱門電影 (Popular)", "movie/popular", {}, 25, total_skipped
        )
        total_success += s
        total_skipped += sk
        total_errors += e
        
        # 2. Top Rated - 高分經典（預計通過率 60-70%）
        s, sk, e = import_from_source(
            conn, "高分經典 (Top Rated)", "movie/top_rated", {}, 10, total_skipped
        )
        total_success += s
        total_skipped += sk
        total_errors += e
        
        # 3. 各類型精選（每類型 5 頁，預計通過率 50-60%）
        genres = [
            (28, "動作"), (35, "喜劇"), (18, "劇情"),
            (27, "恐怖"), (878, "科幻"), (16, "動畫"),
            (10749, "愛情"), (53, "驚悚")
        ]
        
        for genre_id, genre_name in genres:
            s, sk, e = import_from_source(
                conn, f"{genre_name}精選", "discover/movie",
                {"with_genres": genre_id, "sort_by": "vote_average.desc", "vote_count.gte": 100},
                5, total_skipped
            )
            total_success += s
            total_skipped += sk
            total_errors += e
    
    # 最終統計
    with engine.connect() as conn:
        count_result = conn.execute(text("SELECT COUNT(*) FROM movies"))
        final_count = count_result.scalar()
        
        print(f"\n" + "="*60)
        print(f"🎉 多來源導入完成！")
        print(f"📊 數據庫總計: {final_count} 部電影")
        print(f"✅ 本次成功: {total_success}")
        print(f"⏭️  本次跳過: {total_skipped} (資料不齊全)")
        print(f"❌ 本次失敗: {total_errors}")
        print("="*60)

if __name__ == "__main__":
    main()
