"""
電影資料模型 - 從 TMDB API 同步並儲存
"""
from sqlalchemy import Column, String, Integer, Float, Text, Date, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .base import Base


class Movie(Base):
    """電影資料模型 - 儲存從 TMDB 獲取的電影資訊"""
    __tablename__ = "movies"
    
    # 主鍵 - 使用 TMDB ID
    tmdb_id = Column(Integer, primary_key=True)
    
    # 基本資訊
    title = Column(String(255), nullable=False, index=True)
    original_title = Column(String(255), nullable=True)
    overview = Column(Text, nullable=True)
    tagline = Column(String(500), nullable=True)
    
    # 圖片路徑
    poster_path = Column(String(255), nullable=True)
    backdrop_path = Column(String(255), nullable=True)
    
    # 發行資訊
    release_date = Column(Date, nullable=True)
    original_language = Column(String(10), nullable=True)
    
    # 評分與人氣
    vote_average = Column(Float, nullable=True, default=0.0)
    vote_count = Column(Integer, nullable=True, default=0)
    popularity = Column(Float, nullable=True, default=0.0)
    
    # 其他資訊
    runtime = Column(Integer, nullable=True)  # 分鐘
    status = Column(String(50), nullable=True)  # Released, Post Production, etc.
    
    # JSONB 欄位 - 儲存複雜資料
    genres = Column(JSONB, nullable=True)  # [{"id": 28, "name": "Action"}, ...]
    production_countries = Column(JSONB, nullable=True)
    spoken_languages = Column(JSONB, nullable=True)
    
    # 推薦系統相關欄位
    keywords = Column(JSONB, nullable=True)  # ["time travel", "dystopia", ...]
    mood_tags = Column(JSONB, nullable=True)  # ["intense", "dark", "thrilling", ...]
    tone = Column(Text, nullable=True)  # GPT 生成的電影氛圍描述
    
    # 時間戳記
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)
    
    # 關聯 - 反向關聯到 Watchlist 和 Top10List
    in_watchlists = relationship("Watchlist", back_populates="movie", cascade="all, delete-orphan")
    in_top10_lists = relationship("Top10List", back_populates="movie", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Movie(tmdb_id={self.tmdb_id}, title='{self.title}')>"
