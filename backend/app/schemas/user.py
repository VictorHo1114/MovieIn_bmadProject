from pydantic import BaseModel, EmailStr, Field
from uuid import UUID

# Pydantic (Schemas) vs SQLAlchemy (Models)
# Schemas 定義 API 的資料形狀 (Data Shape)
# Models 定義資料庫的資料表 (Table Structure)

# --- 基礎 Schemas (可共用) ---

class ProfileBase(BaseModel):
    """
    用於「讀取」的 Profile 基礎
    """
    display_name: str | None = None
    avatar_url: str | None = None
    
    # (可選) 根據你的 goal_2 擴充
    # locale: str | None = None
    # adult_content_opt_in: bool = False

    class Config:
        from_attributes = True # 關鍵！允許 Pydantic 從 SQLAlchemy model 讀取資料


# --- 請求 Schemas (用於 API 傳入) ---

class UserCreate(BaseModel):
    """
    用於 /auth/signup (註冊) 的請求 Body
    """
    email: EmailStr # 自動驗證 email 格式
    password: str = Field(min_length=8, description="密碼最少8位數")
    # (可選) 讓使用者在註冊時就可以設定暱稱
    display_name: str | None = None 

class UserLogin(BaseModel):
    """
    用於 /auth/login (登入) 的請求 Body
    """
    email: EmailStr
    password: str
    
# (未來) 你可以在這裡新增 ProfileUpdate, PasswordChange 等 Schemas
# class ProfileUpdate(BaseModel):
#    display_name: str | None


# --- 回應 Schemas (用於 API 傳出) ---

class UserPublic(BaseModel):
    """
    用於「回傳」給前端的安全使用者資料
    (沒有 password_hash！)
    """
    user_id: UUID
    email: EmailStr
    
    # 巢狀載入 Profile 資料
    profile: ProfileBase | None = None
    
    # 遊戲化欄位
    total_points: int = 0
    level: int = 1

    class Config:
       from_attributes = True # 關鍵！允許 Pydantic 從 User model 轉換


class Token(BaseModel):
    """
    用於 /auth/login (登入) 的回應
    """
    access_token: str
    token_type: str = "bearer" # 預設為 "bearer"

# --- 內部使用 Schemas (用於 Security) ---

class TokenData(BaseModel):
    """
    儲存在 JWT 權杖 (Token) 內的資料
    """
    user_id: UUID | None = None

# ... (檔案頂部的 UserCreate, UserLogin, UserPublic, Token... 保持不變) ...

# --- (新增) 用於「更新」的 Schemas ---

class ProfileUpdate(BaseModel):
    """
    用於 PATCH /profile/me (更新 Profile) 的請求 Body
    """
    display_name: str | None = None
    avatar_url: str | None = None
    # (未來可以擴充 locale 等)

    class Config:
        from_attributes = True
    
class PasswordChange(BaseModel):
    """
    用於 POST /auth/change-password (更改密碼) 的請求 Body
    """
    old_password: str
    new_password: str = Field(min_length=8, description="新密碼最少8位數")

class ForgotPasswordRequest(BaseModel):
    """
    用於 POST /auth/forgot-password (請求重設) 的 Body
    """
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    """
    用於 POST /auth/reset-password (執行重設) 的 Body
    """
    token: str
    new_password: str = Field(min_length=8, description="新密碼最少8位數")