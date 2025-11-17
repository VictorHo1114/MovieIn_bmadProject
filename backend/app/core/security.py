import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload
from uuid import UUID

# --- 依賴我們剛剛建立的檔案 ---
from db.session import get_db             # 依賴：DB 連線
from app.models.user import User          # 依賴：User DB Model
from app.schemas.user import TokenData    # 依賴：Token Schema
# from app.env import settings            # (推薦) 應從環境變數讀取

# --- 1. JWT (通行證) 設定 ---

# [警告] 這組密鑰(SECRET_KEY)絕對不能外洩！
# 最好是從 .env 檔案讀取 (os.getenv("SECRET_KEY"))
# 這裡為了簡單起見，我們先寫死。
SECRET_KEY = "your-super-secret-key-please-change-it"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # Token 時效：1 天 (60 分鐘 * 24 小時)

# 這會告訴 FastAPI 去哪裡 "拿" Token
# tokenUrl="/auth/login" 意思是：如果 token 無效，請用戶去 /auth/login 取得
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# --- 2. 建立「通行證」的函式 ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    建立 JWT Access Token
    :param data: 要編碼到 Token 中的資料 (e.g., {"sub": user_id})
    """
    to_encode = data.copy()
    
    # 計算過期時間
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # 產生加密的 token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- 3. 驗證「通行證」的警衛 (FastAPI 依賴) ---

def get_current_user(
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme) # 警衛會自動從 Header 取得 Token
) -> User:
    """
    FastAPI Dependency:
    解析 Token，驗證並回傳 User Model 物件。
    如果失敗，會自動拋出 HTTPException。
    """
    
    # 這是 Token 驗證失敗時要回傳的標準錯誤
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 警衛試圖解碼 Token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 從 Token 中取出 "sub" (subject)，我們用它來存 user_id
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        
        # 使用我們在 schemas/user.py 定義的 TokenData 來驗證格式
        token_data = TokenData(user_id=UUID(user_id_str))

    except JWTError:
        # Token 解碼失敗 (過期、或簽名不符)
        raise credentials_exception
    except Exception:
        # 其他錯誤 (例如 UUID 格式不對)
        raise credentials_exception
    
    # 警衛拿著 user_id 去資料庫撈人，並且主動載入 profile
    user = db.query(User).options(joinedload(User.profile)).filter(User.user_id == token_data.user_id).first()
    
    if user is None:
        # 如果 Token 裡的 user_id 在資料庫裡找不到 (例如被刪除了)
        raise credentials_exception
        
    # 驗明正身！把 User 物件回傳給 API 路由
    return user