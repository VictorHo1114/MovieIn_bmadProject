"""
Movies API Routes - 處理電影資料的獲取和儲存
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from typing import List
import httpx
import os
from datetime import datetime

from db.database import get_db
from app.models import Movie
from app.schemas.movie_result import FrontendMovie

router = APIRouter(prefix="/api/movies", tags=["movies"])

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


def _build_frontend_movie(movie: Movie) -> FrontendMovie:
    """將 Movie 模型轉換為 FrontendMovie"""
    poster_url = None
    if movie.poster_path:
        poster_url = f"{IMAGE_BASE_URL}{movie.poster_path}"
    
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


async def _fetch_and_store_movie(tmdb_id: int, db: Session) -> Movie:
    """從 TMDB 獲取電影並儲存到資料庫"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}",
            params={"api_key": TMDB_API_KEY, "language": "zh-TW"},
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movie not found on TMDB",
            )
        
        data = response.json()
        
        # 解析 release_date
        release_date = None
        if data.get("release_date"):
            try:
                release_date = datetime.strptime(data["release_date"], "%Y-%m-%d").date()
            except:
                pass
        
        # 建立或更新電影
        movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
        
        if movie:
            # 更新現有電影
            movie.title = data.get("title", "")
            movie.original_title = data.get("original_title")
            movie.overview = data.get("overview")
            movie.tagline = data.get("tagline")
            movie.poster_path = data.get("poster_path")
            movie.backdrop_path = data.get("backdrop_path")
            movie.release_date = release_date
            movie.original_language = data.get("original_language")
            movie.vote_average = data.get("vote_average", 0.0)
            movie.vote_count = data.get("vote_count", 0)
            movie.popularity = data.get("popularity", 0.0)
            movie.runtime = data.get("runtime")
            movie.status = data.get("status")
            movie.genres = data.get("genres")
            movie.production_countries = data.get("production_countries")
            movie.spoken_languages = data.get("spoken_languages")
        else:
            # 建立新電影
            movie = Movie(
                tmdb_id=tmdb_id,
                title=data.get("title", ""),
                original_title=data.get("original_title"),
                overview=data.get("overview"),
                tagline=data.get("tagline"),
                poster_path=data.get("poster_path"),
                backdrop_path=data.get("backdrop_path"),
                release_date=release_date,
                original_language=data.get("original_language"),
                vote_average=data.get("vote_average", 0.0),
                vote_count=data.get("vote_count", 0),
                popularity=data.get("popularity", 0.0),
                runtime=data.get("runtime"),
                status=data.get("status"),
                genres=data.get("genres"),
                production_countries=data.get("production_countries"),
                spoken_languages=data.get("spoken_languages"),
            )
            db.add(movie)
        
        db.commit()
        db.refresh(movie)
        
        return movie


@router.get("/popular", response_model=List[FrontendMovie])
async def get_popular_movies(
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """取得熱門電影（首頁使用）"""
    # 先從 TMDB 獲取熱門電影列表
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{TMDB_BASE_URL}/movie/popular",
            params={
                "api_key": TMDB_API_KEY,
                "language": "zh-TW",
                "page": page,
            },
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch popular movies from TMDB",
            )
        
        data = response.json()
        results = data.get("results", [])[:limit]
        
        # 將電影儲存到資料庫並回傳
        movies = []
        for movie_data in results:
            tmdb_id = movie_data["id"]
            
            # 檢查資料庫中是否已存在
            movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
            
            if not movie:
                # 獲取完整資料並儲存
                movie = await _fetch_and_store_movie(tmdb_id, db)
            
            movies.append(_build_frontend_movie(movie))
        
        return movies


@router.get("/random/recommendations", response_model=List[FrontendMovie])
async def get_random_movies(
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """從資料庫隨機獲取電影推薦"""
    # 使用 SQLAlchemy 的 func.random() 隨機排序
    movies = db.query(Movie).order_by(func.random()).limit(limit).all()
    
    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="資料庫中沒有電影資料"
        )
    
    return [_build_frontend_movie(movie) for movie in movies]


@router.get("/check/{tmdb_id}", response_model=dict)
async def check_movie_exists(
    tmdb_id: int,
    db: Session = Depends(get_db),
):
    """檢查電影是否存在於資料庫中（不會自動創建）"""
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
    return {"exists": movie is not None, "tmdb_id": tmdb_id}


@router.get("/{tmdb_id}", response_model=FrontendMovie)
async def get_movie(
    tmdb_id: int,
    db: Session = Depends(get_db),
):
    """取得單一電影詳情"""
    # 先查詢資料庫
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
    
    if not movie:
        # 從 TMDB 獲取並儲存
        movie = await _fetch_and_store_movie(tmdb_id, db)
    
    return _build_frontend_movie(movie)

