"""
Watchlist 相關的 Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from .movie_result import FrontendMovie


class WatchlistBase(BaseModel):
    """Watchlist 基礎 Schema"""
    notes: Optional[str] = None
    is_watched: bool = False
    priority: int = Field(default=0, ge=-1, le=1)  # -1=低, 0=中, 1=高


class WatchlistCreate(WatchlistBase):
    """建立 Watchlist 項目的請求 Schema"""
    tmdb_id: Optional[int] = None  # 改為可選，因為會從 URL path 取得


class WatchlistCreateBody(BaseModel):
    """建立 Watchlist 的 Body Schema（不包含 tmdb_id，從 path 取得）"""
    notes: Optional[str] = None
    is_watched: bool = False
    priority: int = Field(default=0, ge=-1, le=1)


class WatchlistUpdate(BaseModel):
    """更新 Watchlist 項目的請求 Schema"""
    notes: Optional[str] = None
    is_watched: Optional[bool] = None
    priority: Optional[int] = Field(default=None, ge=-1, le=1)


class WatchlistItem(WatchlistBase):
    """Watchlist 項目回應 Schema (包含電影資訊)"""
    id: UUID
    user_id: UUID
    tmdb_id: int
    added_at: datetime
    movie: FrontendMovie  # 巢狀電影資料
    
    class Config:
        from_attributes = True


class WatchlistResponse(BaseModel):
    """Watchlist 列表回應"""
    items: list[WatchlistItem]
    total: int
