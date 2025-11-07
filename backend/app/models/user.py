# 檔案：backend/app/models/user.py (完整替換)

import bcrypt
import enum
from datetime import datetime # 確保導入
from sqlalchemy import (
    Column, 
    String, 
    TIMESTAMP, 
    text, 
    Boolean, 
    ForeignKey, 
    Enum as SAEnum,
    DateTime  # <-- [重要！] 確保導入 DateTime
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base

# --- [步驟一：定義 UserProvider (必須在 User 之前)] ---
class UserProvider(str, enum.Enum):
    PASSWORD = "password"
    GOOGLE = "google"
    APPLE = "apple"
    GITHUB = "github"

# --- [步驟二：定義 User] ---
class User(Base):
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=True) 
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    
    email_verified = Column(Boolean, nullable=False, default=False)
    
    # [這行 (第 30 行) 現在可以正確找到 UserProvider 了]
    provider = Column(SAEnum(UserProvider), nullable=False, default=UserProvider.PASSWORD)
    provider_uid = Column(String, nullable=True) 

    # [我們上次新增的欄位]
    reset_token = Column(String, nullable=True, index=True)
    reset_token_expiry = Column(DateTime(timezone=True), nullable=True)

    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password: str):
        """為用戶設置密碼，儲存 hash"""
        if not password:
            self.password_hash = None
            return
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """驗證傳入的密碼是否與 hash 相符"""
        if not self.password_hash or not password:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))


# --- [步驟三：定義 Profile] ---
class Profile(Base):
    __tablename__ = "profiles"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), primary_key=True)
    
    display_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    locale = Column(String, nullable=True, default="en")
    adult_content_opt_in = Column(Boolean, nullable=False, default=False)
    
    user = relationship("User", back_populates="profile")