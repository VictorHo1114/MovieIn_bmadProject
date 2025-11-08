from fastapi import APIRouter, HTTPException
import os
import httpx

router = APIRouter()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
if not TMDB_API_KEY:
    raise ValueError("Missing TMDB_API_KEY environment variable")

@router.get("/{movie_id}")
async def get_movie(movie_id: str):
    """Get movie details from TMDb API"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}",
            params={
                "api_key": TMDB_API_KEY,
                "language": "zh-TW",
            }
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Movie not found")
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "id": str(data["id"]),
            "title": data["title"],
            "original_title": data["original_title"],
            "overview": data["overview"],
            "release_date": data["release_date"],
            "rating": data["vote_average"],
            "vote_count": data["vote_count"],
            "runtime": data["runtime"],
            "poster_url": f"https://image.tmdb.org/t/p/w500{data['poster_path']}" if data.get("poster_path") else None,
            "backdrop_url": f"https://image.tmdb.org/t/p/original{data['backdrop_path']}" if data.get("backdrop_path") else None,
        }