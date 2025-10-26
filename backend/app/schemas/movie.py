from pydantic import BaseModel

class MovieCard(BaseModel):
    id: str
    title: str
    year: int
    rating: float