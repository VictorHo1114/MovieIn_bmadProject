from fastapi import APIRouter, HTTPException
import os
import httpx

router = APIRouter(prefix="/popular", tags=["popular"])

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
if not TMDB_API_KEY:
    raise ValueError("Missing TMDB_API_KEY environment variable")

@router.get("/")
async def get_popular_movies():
    """獲取熱門電影列表"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(
            "https://api.themoviedb.org/3/movie/popular",
            params={
                "api_key": TMDB_API_KEY,
                "language": "zh-TW",
                "page": 1
            }
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Not found")
        response.raise_for_status()
        
        data = response.json()
        movies = data.get("results", [])
        
        # 格式化返回的資料
        return {
            "items": [
                {
                    "id": str(movie["id"]),
                    "title": movie["title"],
                    "overview": movie["overview"],
                    "poster_path": movie["poster_path"],
                    "poster_url": f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie.get("poster_path") else None,
                    "backdrop_path": movie["backdrop_path"],
                    "backdrop_url": f"https://image.tmdb.org/t/p/original{movie['backdrop_path']}" if movie.get("backdrop_path") else None,
                    "release_date": movie["release_date"],
                    "rating": movie["vote_average"],
                    "vote_count": movie["vote_count"]
                }
                for movie in movies
            ],
            "total": len(movies)
        }