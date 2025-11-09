# app/schemas/movie_result.py
from pydantic import BaseModel, Field
from typing import Optional
  

#定義一個「乾淨、前端專用」的電影資料結構  
class FrontendMovie(BaseModel):
    id: int
    title: str
    overview: str
    poster_url: Optional[str] = None # 我們會組裝成完整 URL
    release_year: Optional[int] = None
    vote_average: float = Field(0.0)

    class Config:
        from_attributes = True 
