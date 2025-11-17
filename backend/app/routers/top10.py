"""
Top 10 List API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from db.database import get_db
from app.models import Top10List, Movie, User
from app.schemas.top10 import (
    Top10Create,
    Top10CreateBody,
    Top10Update,
    Top10Item,
    Top10Response,
    Top10Reorder,
)
from app.schemas.movie_result import FrontendMovie
from app.core.security import get_current_user

router = APIRouter(prefix="/api/top10", tags=["top10"])


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


@router.get("", response_model=Top10Response)
async def get_top10_list(
    category: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得使用者的 Top 10 List (可按分類篩選)"""
    query = db.query(Top10List).filter(Top10List.user_id == current_user.user_id)
    
    if category:
        query = query.filter(Top10List.category == category)
    
    items = query.order_by(Top10List.rank.asc()).all()
    
    # 載入關聯的電影資料
    top10_items = []
    for item in items:
        movie = db.query(Movie).filter(Movie.tmdb_id == item.tmdb_id).first()
        if movie:
            top10_items.append(
                Top10Item(
                    id=item.id,
                    user_id=item.user_id,
                    tmdb_id=item.tmdb_id,
                    rank=item.rank,
                    added_at=item.added_at,
                    notes=item.notes,
                    rating_by_user=item.rating_by_user,
                    category=item.category,
                    movie=_build_frontend_movie(movie),
                )
            )
    
    return Top10Response(items=top10_items, total=len(top10_items))



@router.get("/public/{user_id}", response_model=Top10Response, tags=["public"])
async def get_top10_public(
    user_id: str,
    db: Session = Depends(get_db),
):
    """取得任一使用者的公開 Top10（預設公開）"""
    try:
        from uuid import UUID as _UUID

        parsed = _UUID(user_id)
    except Exception:
        parsed = None

    query = db.query(Top10List)
    if parsed is not None:
        query = query.filter(Top10List.user_id == parsed)
    else:
        query = query.filter(Top10List.user_id == user_id)

    items = query.order_by(Top10List.rank.asc()).all()

    top10_items = []
    for item in items:
        movie = db.query(Movie).filter(Movie.tmdb_id == item.tmdb_id).first()
        if movie:
            top10_items.append(
                Top10Item(
                    id=item.id,
                    user_id=item.user_id,
                    tmdb_id=item.tmdb_id,
                    rank=item.rank,
                    added_at=item.added_at,
                    notes=item.notes,
                    rating_by_user=item.rating_by_user,
                    category=item.category,
                    movie=_build_frontend_movie(movie),
                )
            )

    return Top10Response(items=top10_items, total=len(top10_items))


@router.get("/public/{user_id}", response_model=Top10Response, tags=["public"])
async def get_top10_public(
    user_id: str,
    category: str = None,
    db: Session = Depends(get_db),
):
    """取得任一使用者的公開 Top10（預設公開）"""
    try:
        from uuid import UUID as _UUID

        parsed = _UUID(user_id)
    except Exception:
        parsed = None

    if parsed is not None:
        query = db.query(Top10List).filter(Top10List.user_id == parsed)
    else:
        query = db.query(Top10List).filter(Top10List.user_id == user_id)

    if category:
        query = query.filter(Top10List.category == category)

    items = query.order_by(Top10List.rank.asc()).all()

    top10_items = []
    for item in items:
        movie = db.query(Movie).filter(Movie.tmdb_id == item.tmdb_id).first()
        if movie:
            top10_items.append(
                Top10Item(
                    id=item.id,
                    user_id=item.user_id,
                    tmdb_id=item.tmdb_id,
                    rank=item.rank,
                    added_at=item.added_at,
                    notes=item.notes,
                    rating_by_user=item.rating_by_user,
                    category=item.category,
                    movie=_build_frontend_movie(movie),
                )
            )

    return Top10Response(items=top10_items, total=len(top10_items))


@router.post("/{tmdb_id}", response_model=Top10Item, status_code=status.HTTP_201_CREATED)
async def add_to_top10(
    tmdb_id: int,
    data: Top10CreateBody = Top10CreateBody(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """將電影加入 Top 10 List"""
    category = data.category if data else None
    
    # 檢查該分類的 Top 10 是否已滿
    existing_count = (
        db.query(Top10List)
        .filter(
            Top10List.user_id == current_user.user_id,
            Top10List.category == category,
        )
        .count()
    )
    
    if existing_count >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Top 10 list is full (maximum 10 movies)",
        )
    
    # 檢查電影是否已在該分類的 Top 10 中
    existing = (
        db.query(Top10List)
        .filter(
            Top10List.user_id == current_user.user_id,
            Top10List.tmdb_id == tmdb_id,
            Top10List.category == category,
        )
        .first()
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie already in this Top 10 list",
        )
    
    # 確認電影存在
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found in database. Please fetch from TMDB first.",
        )
    
    # 決定 rank
    if data and data.rank:
        rank = data.rank
        # 如果指定的 rank 已存在，則將該 rank 及之後的項目往後移
        existing_items = (
            db.query(Top10List)
            .filter(
                Top10List.user_id == current_user.user_id,
                Top10List.category == category,
                Top10List.rank >= rank,
            )
            .all()
        )
        for item in existing_items:
            item.rank += 1
    else:
        # 自動分配最後一個 rank
        max_rank = (
            db.query(Top10List.rank)
            .filter(
                Top10List.user_id == current_user.user_id,
                Top10List.category == category,
            )
            .order_by(Top10List.rank.desc())
            .first()
        )
        rank = (max_rank[0] + 1) if max_rank else 1
    
    # 建立 Top10List 項目
    top10_item = Top10List(
        user_id=current_user.user_id,
        tmdb_id=tmdb_id,
        rank=rank,
        notes=data.notes if data else None,
        rating_by_user=data.rating_by_user if data else None,
        category=category,
    )
    
    db.add(top10_item)
    db.commit()
    db.refresh(top10_item)
    
    return Top10Item(
        id=top10_item.id,
        user_id=top10_item.user_id,
        tmdb_id=top10_item.tmdb_id,
        rank=top10_item.rank,
        added_at=top10_item.added_at,
        notes=top10_item.notes,
        rating_by_user=top10_item.rating_by_user,
        category=top10_item.category,
        movie=_build_frontend_movie(movie),
    )


@router.delete("/{tmdb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_top10(
    tmdb_id: int,
    category: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """從 Top 10 List 移除電影"""
    item = (
        db.query(Top10List)
        .filter(
            Top10List.user_id == current_user.user_id,
            Top10List.tmdb_id == tmdb_id,
            Top10List.category == category,
        )
        .first()
    )
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found in Top 10 list",
        )
    
    removed_rank = item.rank
    
    db.delete(item)
    
    # 重新調整後續項目的 rank
    subsequent_items = (
        db.query(Top10List)
        .filter(
            Top10List.user_id == current_user.user_id,
            Top10List.category == category,
            Top10List.rank > removed_rank,
        )
        .all()
    )
    
    for item in subsequent_items:
        item.rank -= 1
    
    db.commit()
    
    return None


@router.put("/reorder", response_model=Top10Response)
async def reorder_top10(
    data: Top10Reorder,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重新排序 Top 10 List"""
    # 驗證所有項目都屬於當前使用者
    for item_data in data.items:
        item = db.query(Top10List).filter(Top10List.id == item_data.id).first()
        if not item or item.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item {item_data.id} not found or does not belong to you",
            )
    
    # 更新 rank
    for item_data in data.items:
        item = db.query(Top10List).filter(Top10List.id == item_data.id).first()
        item.rank = item_data.rank
    
    db.commit()
    
    # 回傳更新後的清單
    items = (
        db.query(Top10List)
        .filter(Top10List.user_id == current_user.user_id)
        .order_by(Top10List.rank.asc())
        .all()
    )
    
    top10_items = []
    for item in items:
        movie = db.query(Movie).filter(Movie.tmdb_id == item.tmdb_id).first()
        if movie:
            top10_items.append(
                Top10Item(
                    id=item.id,
                    user_id=item.user_id,
                    tmdb_id=item.tmdb_id,
                    rank=item.rank,
                    added_at=item.added_at,
                    notes=item.notes,
                    rating_by_user=item.rating_by_user,
                    category=item.category,
                    movie=_build_frontend_movie(movie),
                )
            )
    
    return Top10Response(items=top10_items, total=len(top10_items))


@router.patch("/{tmdb_id}", response_model=Top10Item)
async def update_top10_item(
    tmdb_id: int,
    data: Top10Update,
    category: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新 Top 10 項目"""
    item = (
        db.query(Top10List)
        .filter(
            Top10List.user_id == current_user.user_id,
            Top10List.tmdb_id == tmdb_id,
            Top10List.category == category,
        )
        .first()
    )
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found in Top 10 list",
        )
    
    # 更新欄位
    if data.notes is not None:
        item.notes = data.notes
    if data.rating_by_user is not None:
        item.rating_by_user = data.rating_by_user
    if data.category is not None:
        item.category = data.category
    if data.rank is not None and data.rank != item.rank:
        # 處理 rank 變更
        old_rank = item.rank
        new_rank = data.rank
        
        if new_rank < old_rank:
            # 向前移動 - 將中間的項目往後移
            affected_items = (
                db.query(Top10List)
                .filter(
                    Top10List.user_id == current_user.user_id,
                    Top10List.category == category,
                    Top10List.rank >= new_rank,
                    Top10List.rank < old_rank,
                )
                .all()
            )
            for affected in affected_items:
                affected.rank += 1
        else:
            # 向後移動 - 將中間的項目往前移
            affected_items = (
                db.query(Top10List)
                .filter(
                    Top10List.user_id == current_user.user_id,
                    Top10List.category == category,
                    Top10List.rank > old_rank,
                    Top10List.rank <= new_rank,
                )
                .all()
            )
            for affected in affected_items:
                affected.rank -= 1
        
        item.rank = new_rank
    
    db.commit()
    db.refresh(item)
    
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
    
    return Top10Item(
        id=item.id,
        user_id=item.user_id,
        tmdb_id=item.tmdb_id,
        rank=item.rank,
        added_at=item.added_at,
        notes=item.notes,
        rating_by_user=item.rating_by_user,
        category=item.category,
        movie=_build_frontend_movie(movie),
    )
