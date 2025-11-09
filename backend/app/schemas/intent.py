from pydantic import BaseModel
from typing import List, Optional, Tuple

class IntentConstraints(BaseModel):
    year_range: Optional[Tuple[int,int]] = None
    languages: Optional[List[str]] = None
    genres: Optional[List[str]] = None
    country: Optional[str] = None
    must_have_providers: Optional[List[str]] = None
    runtime_range: Optional[Tuple[int,int]] = None
    vote_average_min: Optional[float] = None
    vote_count_min: Optional[int] = None
    include_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None


class MovieIntent(BaseModel):
    feature_labels: List[str]
    must_not_labels: Optional[List[str]] = []
    natural_query: Optional[str] = None
    constraints: Optional[IntentConstraints] = None
    locale: Optional[str] = "zh-TW"
