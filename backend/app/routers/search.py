from fastapi import APIRouter, Query, HTTPException
import os
from typing import Any, Dict, List
import httpx

from app.schemas import SearchResult

router = APIRouter()


def _format_tmdb_item(item: Dict[str, Any]) -> Dict[str, Any]:
    # map TMDB item to our MovieCard-like shape
    release_date = item.get("release_date") or ""
    year = release_date[:4] if release_date else None
    return {
        "id": str(item.get("id")),
        "title": item.get("title") or item.get("name") or "",
        "year": int(year) if year and year.isdigit() else None,
        "rating": round(float(item.get("vote_average") or 0), 1),
    }


@router.get("", response_model=SearchResult)
async def search(q: str = Query(..., min_length=1)):
    """Search movies via TMDb and return a list of items matching the frontend SearchResult schema."""
    TMDB_API_KEY = os.getenv("TMDB_API_KEY")
    if not TMDB_API_KEY:
        raise HTTPException(status_code=500, detail="TMDB API Key is not configured.")

    tmdb_url = "https://api.themoviedb.org/3/search/movie"
    params = {"api_key": TMDB_API_KEY, "query": q, "language": "zh-TW"}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(tmdb_url, params=params)
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Failed to reach TMDb: {str(e)}")

    if resp.status_code != 200:
        # propagate TMDB's error as a 502 (bad gateway)
        raise HTTPException(status_code=502, detail=f"TMDb returned {resp.status_code}")

    payload = resp.json()
    results = payload.get("results", [])
    items: List[Dict[str, Any]] = []
    for it in results:
        item = _format_tmdb_item(it)
        # include poster_path and poster_url if available
        poster = it.get("poster_path")
        if poster:
            item["poster_path"] = poster
            # full URL (w300)
            item["poster_url"] = f"https://image.tmdb.org/t/p/w300{poster}"
        # include overview if present
        overview = it.get("overview")
        if overview:
            item["overview"] = overview
        items.append(item)

    return {"items": items}
