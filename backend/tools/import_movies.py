import os
import sys
import json
import time
import httpx
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 設置 UTF-8 編碼輸出 (Windows 兼容)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

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

def fetch_movie_details(tmdb_id, retries=3):
    """獲取電影詳細資訊（帶重試機制）"""
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "zh-TW"
    }
    
    for attempt in range(retries):
        try:
            response = httpx.get(url, params=params, timeout=15.0)
            response.raise_for_status()
            return response.json()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
                continue
            return None
    return None

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
    """儲存電影到數據庫，返回是否為新電影"""
    try:
        # 先檢查是否已存在
        check_query = text("SELECT COUNT(*) FROM movies WHERE tmdb_id = :tmdb_id")
        exists = conn.execute(check_query, {"tmdb_id": movie_data["id"]}).scalar()
        
        if exists > 0:
            return False  # 已存在，不是新電影
        
        # 提取 genres（TMDB 返回的是對象陣列）
        genres = [g["name"] for g in movie_data.get("genres", [])]
        genres_json = json.dumps(genres, ensure_ascii=False)
        
        query = text("""
            INSERT INTO movies (
                tmdb_id, title, original_title, overview, 
                poster_path, backdrop_path, release_date, 
                genres, vote_average, vote_count, 
                popularity, runtime, original_language
            ) VALUES (
                :tmdb_id, :title, :original_title, :overview,
                :poster_path, :backdrop_path, :release_date,
                CAST(:genres AS jsonb), :vote_average, :vote_count,
                :popularity, :runtime, :original_language
            )
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
            "original_language": movie_data.get("original_language", "")
        })
        
        return True  # 成功插入新電影
        
    except Exception as e:
        print(f"  ❌ 儲存失敗 (tmdb_id={movie_data.get('id')}): {e}")
        return False

def import_from_source_with_offset(conn, source_name, endpoint, params, start_page, page_count, skip_count, max_success=30):
    """從指定來源導入電影（支援起始頁碼和配額限制）"""
    print(f"\n{'='*60}")
    print(f"📚 來源: {source_name} (配額上限: {max_success}部新電影)")
    print(f"📄 頁數: 從第 {start_page} 頁開始")
    print(f"{'='*60}\n")
    
    success = 0
    skipped = 0
    errors = 0
    page = start_page
    
    # 持續搜索直到達到配額或搜尋完所有頁面
    while success < max_success and page < start_page + page_count + 50:  # 最多搜索額外50頁
        try:
            data = fetch_movies(endpoint, params, page)
            movies = data.get("results", [])
            
            if not movies:
                print(f"  ℹ️  第 {page} 頁無結果，停止搜索")
                break
            
            for movie in movies:
                # 如果已達配額，停止
                if success >= max_success:
                    break
                
                try:
                    # 先檢查是否已存在
                    check_query = text("SELECT COUNT(*) FROM movies WHERE tmdb_id = :tmdb_id")
                    exists = conn.execute(check_query, {"tmdb_id": movie["id"]}).scalar()
                    
                    if exists > 0:
                        skipped += 1
                        continue
                    
                    # 獲取詳細資料
                    details = fetch_movie_details(movie["id"])
                    
                    if not details:
                        errors += 1
                        continue
                    
                    # 檢查資料完整性
                    is_valid, reason = is_valid_movie(details)
                    if not is_valid:
                        skipped += 1
                        continue
                    
                    # 儲存電影
                    is_new = store_movie(conn, details)
                    if is_new:
                        success += 1
                        print(f"  ✅ [{success}/{max_success}] {details['title'][:40]}")
                    else:
                        skipped += 1
                    
                    time.sleep(0.3)  # API 限速
                    
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    errors += 1
                    continue
            
            # 達到配額就停止
            if success >= max_success:
                print(f"\n  ✅ 已達配額上限 {max_success} 部，切換到下一個類別\n")
                break
            
            page += 1
            
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"  ❌ 第 {page} 頁失敗: {e}")
            page += 1
            continue
    
    print(f"  📊 本類別統計: 成功 {success}, 跳過 {skipped}, 錯誤 {errors}")
    return success, skipped, errors

def main():
    print("🎬 開始多來源電影數據導入...")
    print("📊 策略: 各類型高分 + 不同年代經典 + 不同語言")
    print("🎯 目標: 1000 部高品質電影")
    print("✅ 品質檢查: 簡介(≥20字)、類型、海報、評分(≥5)\n")
    
    total_success = 0
    total_skipped = 0
    total_errors = 0
    
    with engine.begin() as conn:
        # 檢查當前數量
        current_count = conn.execute(text("SELECT COUNT(*) FROM movies")).scalar()
        needed = 1000 - current_count
        print(f"📊 當前資料庫: {current_count} 部電影")
        print(f"🎯 目標新增: {needed} 部\n")
        
        if needed <= 0:
            print("✅ 已達到 1000 部目標！")
            return
        
        # 1. 各類型高分電影 - 每個類別 30 部
        genres = [
            (28, "動作"), (18, "劇情"), (878, "科幻"),
            (16, "動畫"), (35, "喜劇"), (53, "驚悚"),
            (27, "恐怖"), (10749, "愛情"), (14, "奇幻"),
            (80, "犯罪"), (12, "冒險")
        ]
        
        print("=" * 60)
        print("階段 1: 各類型高分電影 (每類別 30 部)")
        print("=" * 60)
        
        for genre_id, genre_name in genres:
            if total_success >= needed:
                break
            
            s, sk, e = import_from_source_with_offset(
                conn, f"🎭 {genre_name}類型", "discover/movie",
                {"with_genres": genre_id, "sort_by": "vote_average.desc", "vote_count.gte": 200},
                start_page=20, page_count=10, skip_count=total_skipped, max_success=30
            )
            total_success += s
            total_skipped += sk
            total_errors += e
        
        # 2. 不同年代經典電影 - 每個年代 30 部
        decades = [
            ("2020年代", {"primary_release_date.gte": "2020-01-01", "primary_release_date.lte": "2024-12-31"}),
            ("2010年代", {"primary_release_date.gte": "2010-01-01", "primary_release_date.lte": "2019-12-31"}),
            ("2000年代", {"primary_release_date.gte": "2000-01-01", "primary_release_date.lte": "2009-12-31"}),
            ("90年代", {"primary_release_date.gte": "1990-01-01", "primary_release_date.lte": "1999-12-31"}),
            ("80年代", {"primary_release_date.gte": "1980-01-01", "primary_release_date.lte": "1989-12-31"}),
        ]
        
        print("\n" + "=" * 60)
        print("階段 2: 不同年代經典電影 (每年代 30 部)")
        print("=" * 60)
        
        for decade_name, params in decades:
            if total_success >= needed:
                break
            
            params.update({"sort_by": "vote_average.desc", "vote_count.gte": 150})
            s, sk, e = import_from_source_with_offset(
                conn, f"📅 {decade_name}", "discover/movie",
                params, start_page=20, page_count=10, skip_count=total_skipped, max_success=30
            )
            total_success += s
            total_skipped += sk
            total_errors += e
        
        # 3. 不同語言電影 - 每個語言 30 部
        languages = [
            ("ja", "日本"),
            ("ko", "韓國"),
            ("fr", "法國"),
            ("es", "西班牙"),
            ("de", "德國"),
            ("it", "義大利"),
        ]
        
        print("\n" + "=" * 60)
        print("階段 3: 不同語言電影 (每語言 30 部)")
        print("=" * 60)
        
        for lang_code, lang_name in languages:
            if total_success >= needed:
                break
            
            s, sk, e = import_from_source_with_offset(
                conn, f"🌍 {lang_name}電影", "discover/movie",
                {"with_original_language": lang_code, "sort_by": "vote_average.desc", "vote_count.gte": 80},
                start_page=20, page_count=10, skip_count=total_skipped, max_success=30
            )
            total_success += s
            total_skipped += sk
            total_errors += e
    
    # 最終統計
    with engine.connect() as conn:
        final_count = conn.execute(text("SELECT COUNT(*) FROM movies")).scalar()
        qualified = conn.execute(text("""
            SELECT COUNT(*) FROM movies
            WHERE title IS NOT NULL AND title != ''
              AND overview IS NOT NULL AND overview != ''
              AND LENGTH(overview) >= 20
              AND genres IS NOT NULL AND genres::text != '[]'
              AND poster_path IS NOT NULL AND poster_path != ''
              AND vote_count >= 5
        """)).scalar()
        
        print(f"\n" + "="*60)
        print(f"🎉 導入完成！")
        print(f"="*60)
        print(f"📊 資料庫總計: {final_count} 部電影")
        print(f"✅ 本次新增: {total_success} 部")
        print(f"⏭️  本次跳過: {total_skipped} 部 (已存在或資料不完整)")
        print(f"❌ 本次失敗: {total_errors} 部")
        print(f"✨ 完全合格: {qualified} 部 ({qualified*100/final_count:.1f}%)")
        print("="*60)

if __name__ == "__main__":
    main()
