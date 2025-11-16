"""
Watchlist API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from db.database import get_db
from app.models import Watchlist, Movie, User
from app.schemas.watchlist import (
    WatchlistCreate,
    WatchlistCreateBody,
    WatchlistUpdate,
    WatchlistItem,
    WatchlistResponse,
)
from app.schemas.movie_result import FrontendMovie
from app.core.security import get_current_user

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


def _build_frontend_movie(movie: Movie) -> FrontendMovie:
    """將 Movie 模型轉換為 FrontendMovie"""
    poster_url = None
    if movie.poster_path:
        poster_url = f"https://image.tmdb.org/t/p/w500{movie.poster_path}"
    
    release_year = None
    if movie.release_date:
        release_year = movie.release_date.year
    
    return FrontendMovie(
        id=movie.tmdb_id,
        title=movie.title,
        overview=movie.overview or "",
        poster_url=poster_url,
        release_year=release_year,
        vote_average=movie.vote_average or 0.0,
    )


@router.get("", response_model=WatchlistResponse)
async def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得使用者的 Watchlist"""
    items = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == current_user.user_id)
        .order_by(Watchlist.added_at.desc())
        .all()
    )
    
    # 載入關聯的電影資料
    watchlist_items = []
    for item in items:
        movie = db.query(Movie).filter(Movie.tmdb_id == item.tmdb_id).first()
        if movie:
            watchlist_items.append(
                WatchlistItem(
                    id=item.id,
                    user_id=item.user_id,
                    tmdb_id=item.tmdb_id,
                    added_at=item.added_at,
                    notes=item.notes,
                    is_watched=item.is_watched,
                    priority=item.priority,
                    movie=_build_frontend_movie(movie),
                )
            )
    
    return WatchlistResponse(items=watchlist_items, total=len(watchlist_items))


@router.post("/{tmdb_id}", response_model=WatchlistItem, status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    tmdb_id: int,
    data: WatchlistCreateBody = WatchlistCreateBody(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """將電影加入 Watchlist"""
    # 檢查是否已存在
    existing = (
        db.query(Watchlist)
        .filter(
            Watchlist.user_id == current_user.user_id,
            Watchlist.tmdb_id == tmdb_id,
        )
        .first()
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie already in watchlist",
        )
    
    # 確認電影存在（如果不存在，需要從 TMDB 獲取並儲存）
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
    if not movie:
        # TODO: 從 TMDB API 獲取電影資料並儲存
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found in database. Please fetch from TMDB first.",
        )
    
    # 建立 Watchlist 項目
    watchlist_item = Watchlist(
        user_id=current_user.user_id,
        tmdb_id=tmdb_id,
        notes=data.notes if data else None,
        priority=data.priority if data else 0,
    )
    
    db.add(watchlist_item)
    db.commit()
    db.refresh(watchlist_item)
    
    return WatchlistItem(
        id=watchlist_item.id,
        user_id=watchlist_item.user_id,
        tmdb_id=watchlist_item.tmdb_id,
        added_at=watchlist_item.added_at,
        notes=watchlist_item.notes,
        is_watched=watchlist_item.is_watched,
        priority=watchlist_item.priority,
        movie=_build_frontend_movie(movie),
    )


@router.delete("/{tmdb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    tmdb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """從 Watchlist 移除電影"""
    item = (
        db.query(Watchlist)
        .filter(
            Watchlist.user_id == current_user.user_id,
            Watchlist.tmdb_id == tmdb_id,
        )
        .first()
    )
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found in watchlist",
        )
    
    db.delete(item)
    db.commit()
    
    return None


@router.patch("/{tmdb_id}", response_model=WatchlistItem)
async def update_watchlist_item(
    tmdb_id: int,
    data: WatchlistUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新 Watchlist 項目"""
    item = (
        db.query(Watchlist)
        .filter(
            Watchlist.user_id == current_user.user_id,
            Watchlist.tmdb_id == tmdb_id,
        )
        .first()
    )
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found in watchlist",
        )
    
    # 更新欄位
    if data.notes is not None:
        item.notes = data.notes
    if data.is_watched is not None:
        item.is_watched = data.is_watched
    if data.priority is not None:
        item.priority = data.priority
    
    db.commit()
    db.refresh(item)
    
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
    
    return WatchlistItem(
        id=item.id,
        user_id=item.user_id,
        tmdb_id=item.tmdb_id,
        added_at=item.added_at,
        notes=item.notes,
        is_watched=item.is_watched,
        priority=item.priority,
        movie=_build_frontend_movie(movie),
    )


@router.get("/public/{user_id}", response_model=WatchlistResponse, tags=["public"])
async def get_watchlist_public(
    user_id: str,
    db: Session = Depends(get_db),
):
    """取得任一使用者的公開 Watchlist（預設公開）"""
    # 嘗試解析 UUID，容錯處理
    try:
        from uuid import UUID as _UUID

        parsed = _UUID(user_id)
    except Exception:
        parsed = None

    if parsed is not None:
        items = (
            db.query(Watchlist)
            .filter(Watchlist.user_id == parsed)
            .order_by(Watchlist.added_at.desc())
            .all()
        )
    else:
        items = (
            db.query(Watchlist)
            .filter(Watchlist.user_id == user_id)
            .order_by(Watchlist.added_at.desc())
            .all()
        )

    watchlist_items = []
    for item in items:
        movie = db.query(Movie).filter(Movie.tmdb_id == item.tmdb_id).first()
        if movie:
            watchlist_items.append(
                WatchlistItem(
                    id=item.id,
                    user_id=item.user_id,
                    tmdb_id=item.tmdb_id,
                    added_at=item.added_at,
                    notes=item.notes,
                    is_watched=item.is_watched,
                    priority=item.priority,
                    movie=_build_frontend_movie(movie),
                )
            )

    return WatchlistResponse(items=watchlist_items, total=len(watchlist_items))
