from pydantic import BaseModel
from typing import List
from .movie import MovieCard

class HomeFeed(BaseModel):
    trending: List[MovieCard]