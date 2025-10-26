from fastapi import APIRouter
from app.schemas import HomeFeed, MovieCard  # 從 barrel 匯入

router = APIRouter()

@router.get("", response_model=HomeFeed)
def get_home():
    items = [
        MovieCard(id="1", title="Inception", year=2010, rating=8.8),
        MovieCard(id="2", title="Interstellar", year=2014, rating=8.6),
    ]
    return {"trending": items}
