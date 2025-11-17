# import os
# import sys
# import json
# import time
# import httpx
# from sqlalchemy import create_engine, text
# from dotenv import load_dotenv

# # 加載環境變數
# load_dotenv()

# TMDB_API_KEY = os.getenv("TMDB_API_KEY")
# DATABASE_URL = os.getenv("DATABASE_URL")

# engine = create_engine(DATABASE_URL)

# def fetch_movie_details(tmdb_id):
#     """獲取電影詳細資訊"""
#     url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
#     params = {"api_key": TMDB_API_KEY, "language": "zh-TW"}
#     response = httpx.get(url, params=params, timeout=10.0)
#     response.raise_for_status()
#     return response.json()

# def is_valid_movie(movie_data):
#     """檢查電影資料是否齊全"""
#     overview = movie_data.get("overview", "").strip()
#     if not overview or len(overview) < 20:
#         return False, "簡介太短"
#     if not movie_data.get("genres") or len(movie_data.get("genres", [])) == 0:
#         return False, "缺少類型"
#     if not movie_data.get("poster_path"):
#         return False, "缺少海報"
#     if movie_data.get("vote_count", 0) < 5:
#         return False, f"評分數太少"
#     return True, "OK"

# def fetch_discover_movies(params, page=1):
#     """使用 discover API"""
#     url = "https://api.themoviedb.org/3/discover/movie"
#     params.update({"api_key": TMDB_API_KEY, "language": "zh-TW", "page": page})
#     response = httpx.get(url, params=params, timeout=10.0)
#     response.raise_for_status()
#     return response.json()

# def store_movie(conn, movie_data):
#     """儲存電影"""
#     genres = [g["name"] for g in movie_data.get("genres", [])]
#     genres_json = json.dumps(genres, ensure_ascii=False)
    
#     query = text("""
#         INSERT INTO movies (
#             tmdb_id, title, original_title, overview, 
#             poster_path, backdrop_path, release_date, 
#             genres, vote_average, vote_count, 
#             popularity, runtime, original_language, adult
#         ) VALUES (
#             :tmdb_id, :title, :original_title, :overview,
#             :poster_path, :backdrop_path, :release_date,
#             CAST(:genres AS jsonb), :vote_average, :vote_count,
#             :popularity, :runtime, :original_language, :adult
#         )
#         ON CONFLICT (tmdb_id) DO NOTHING
#     """)
    
#     conn.execute(query, {
#         "tmdb_id": movie_data["id"],
#         "title": movie_data.get("title", ""),
#         "original_title": movie_data.get("original_title", ""),
#         "overview": movie_data.get("overview", ""),
#         "poster_path": movie_data.get("poster_path"),
#         "backdrop_path": movie_data.get("backdrop_path"),
#         "release_date": movie_data.get("release_date") or None,
#         "genres": genres_json,
#         "vote_average": float(movie_data.get("vote_average", 0.0)),
#         "vote_count": int(movie_data.get("vote_count", 0)),
#         "popularity": float(movie_data.get("popularity", 0.0)),
#         "runtime": movie_data.get("runtime"),
#         "original_language": movie_data.get("original_language", ""),
#         "adult": bool(movie_data.get("adult", False))
#     })

# print(" 擴充電影資料到 1000 部...")

# with engine.begin() as conn:
#     current = conn.execute(text("SELECT COUNT(*) FROM movies")).scalar()
#     print(f" 當前: {current} 部")
#     needed = 1000 - current
#     print(f" 需要: {needed} 部\n")
    
#     success = 0
#     skipped = 0
    
#     # 策略：多來源 + 高品質
#     sources = [
#         ("熱門電影", {"sort_by": "popularity.desc", "vote_count.gte": 50}, 15),
#         ("高分電影", {"sort_by": "vote_average.desc", "vote_count.gte": 100}, 10),
#         ("近期電影", {"primary_release_year": 2024, "sort_by": "vote_count.desc"}, 5),
#         ("2023電影", {"primary_release_year": 2023, "sort_by": "popularity.desc"}, 5),
#         ("經典電影", {"primary_release_year": 2010, "sort_by": "vote_average.desc", "vote_count.gte": 500}, 5),
#     ]
    
#     for source_name, params, pages in sources:
#         if success >= needed:
#             break
            
#         print(f"\n {source_name} ({pages} 頁)...")
#         for page in range(1, pages + 1):
#             if success >= needed:
#                 break
#             try:
#                 data = fetch_discover_movies(params, page)
#                 movies = data.get("results", [])
                
#                 for movie in movies:
#                     if success >= needed:
#                         break
#                     try:
#                         details = fetch_movie_details(movie["id"])
#                         is_valid, reason = is_valid_movie(details)
#                         if not is_valid:
#                             skipped += 1
#                             continue
                        
#                         store_movie(conn, details)
#                         success += 1
#                         print(f"   [{success}/{needed}] {details[\"title\"][:40]}")
#                         time.sleep(0.25)
#                     except Exception as e:
#                         pass
#             except Exception as e:
#                 print(f"   頁面 {page} 失敗")
    
#     final = conn.execute(text("SELECT COUNT(*) FROM movies")).scalar()
#     print(f"\n 完成！總計: {final} 部電影")
#     print(f" 新增: {success} 部")
#     print(f" 跳過: {skipped} 部")
