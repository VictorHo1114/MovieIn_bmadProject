from pydantic import BaseModel
from typing import List
from .movie import MovieCard

class SearchResult(BaseModel):
    items: List[MovieCard]