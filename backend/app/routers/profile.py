from fastapi import APIRouter
from app.schemas import Profile, MovieCard

router = APIRouter()

@router.get("/me", response_model=Profile)
def get_profile_me():
    return {
        "username": "demo_user",
        "watchlist": [MovieCard(id="238", title="The Godfather", year=1972, rating=9.2)]
    }
