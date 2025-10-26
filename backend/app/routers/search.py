from fastapi import APIRouter, Query
from app.schemas import SearchResult, MovieCard

router = APIRouter()

@router.get("", response_model=SearchResult)
def search(q: str = Query(...)):
    return {"items": [MovieCard(id="k1", title=f"{q} result", year=2020, rating=7.7)]}
