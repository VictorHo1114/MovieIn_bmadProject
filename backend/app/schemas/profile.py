from pydantic import BaseModel
from typing import List
from .movie import MovieCard

class Profile(BaseModel):
    username: str
    watchlist: List[MovieCard]