"""
社群功能相關的資料模型
包含：Watchlist, Top10List, Friendship, SharedList, ListInteraction
"""
from sqlalchemy import Column, String, Integer, Boolean, Float, Text, TIMESTAMP, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base


class Watchlist(Base):
    """待看清單 - 7 欄位"""
    __tablename__ = "watchlist"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    tmdb_id = Column(Integer, ForeignKey('movies.tmdb_id', ondelete='CASCADE'), nullable=False)
    added_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    notes = Column(Text, nullable=True)
    is_watched = Column(Boolean, default=False, nullable=False)
    priority = Column(Integer, default=0, nullable=False)  # 1=高, 0=中, -1=低
    
    # 關聯
    user = relationship("User", back_populates="watchlist")
    movie = relationship("Movie", back_populates="in_watchlists")


class Top10List(Base):
    """Top 10 榜單 - 8 欄位"""
    __tablename__ = "top10_list"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    tmdb_id = Column(Integer, ForeignKey('movies.tmdb_id', ondelete='CASCADE'), nullable=False)
    rank = Column(Integer, nullable=False)  # 1-10
    added_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    notes = Column(Text, nullable=True)
    rating_by_user = Column(Float, nullable=True)
    category = Column(String(50), nullable=True)  # 例如: 動作片、喜劇片 Top 10
    
    # 關聯
    user = relationship("User", back_populates="top10_lists")
    movie = relationship("Movie", back_populates="in_top10_lists")


class Friendship(Base):
    """好友關係 - 7 欄位"""
    __tablename__ = "friendships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    friend_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    status = Column(String(20), nullable=False, default='pending')  # pending/accepted/blocked
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    accepted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    message = Column(Text, nullable=True)
    
    # 關聯
    user = relationship("User", foreign_keys=[user_id], back_populates="friendships_initiated")
    friend = relationship("User", foreign_keys=[friend_id], back_populates="friendships_received")


class SharedList(Base):
    """片單分享 - 9 欄位"""
    __tablename__ = "shared_lists"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    list_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    like_count = Column(Integer, default=0, nullable=False)
    
    # 關聯
    owner = relationship("User", back_populates="shared_lists")
    interactions = relationship("ListInteraction", back_populates="shared_list", cascade="all, delete-orphan")


class ListInteraction(Base):
    """片單互動（按讚、評論等）- 6 欄位"""
    __tablename__ = "list_interactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    list_id = Column(UUID(as_uuid=True), ForeignKey('shared_lists.id', ondelete='CASCADE'), nullable=False)
    interaction_type = Column(String(20), nullable=False)  # like/view/share
    comment_text = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False)
    
    # 關聯
    user = relationship("User", back_populates="list_interactions")
    shared_list = relationship("SharedList", back_populates="interactions")
