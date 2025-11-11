"""
Top 10 List 相關的 Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from .movie_result import FrontendMovie


class Top10Base(BaseModel):
    """Top 10 基礎 Schema"""
    notes: Optional[str] = None
    rating_by_user: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    category: Optional[str] = Field(default=None, max_length=50)


class Top10Create(Top10Base):
    """建立 Top 10 項目的請求 Schema"""
    tmdb_id: Optional[int] = None  # 改為可選，因為會從 URL path 取得
    rank: Optional[int] = Field(default=None, ge=1, le=10)  # 如果不提供，自動分配


class Top10CreateBody(BaseModel):
    """建立 Top10 的 Body Schema（不包含 tmdb_id，從 path 取得）"""
    notes: Optional[str] = None
    rating_by_user: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    category: Optional[str] = Field(default=None, max_length=50)
    rank: Optional[int] = Field(default=None, ge=1, le=10)


class Top10Update(BaseModel):
    """更新 Top 10 項目的請求 Schema"""
    rank: Optional[int] = Field(default=None, ge=1, le=10)
    notes: Optional[str] = None
    rating_by_user: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    category: Optional[str] = None


class Top10Item(Top10Base):
    """Top 10 項目回應 Schema (包含電影資訊)"""
    id: UUID
    user_id: UUID
    tmdb_id: int
    rank: int
    added_at: datetime
    movie: FrontendMovie  # 巢狀電影資料
    
    class Config:
        from_attributes = True


class Top10Response(BaseModel):
    """Top 10 列表回應"""
    items: list[Top10Item]
    total: int


class Top10ReorderItem(BaseModel):
    """重新排序的項目"""
    id: UUID
    rank: int = Field(ge=1, le=10)


class Top10Reorder(BaseModel):
    """重新排序請求"""
    items: list[Top10ReorderItem]
