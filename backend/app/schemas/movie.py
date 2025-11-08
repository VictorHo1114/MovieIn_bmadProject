from pydantic import BaseModel
from typing import Optional


class MovieCard(BaseModel):
    id: str
    title: str
    year: Optional[int] = None
    rating: Optional[float] = None
    poster_path: Optional[str] = None
    poster_url: Optional[str] = None
    overview: Optional[str] = None