import secrets # <-- [新增！] 用於產生安全的隨機 token
from datetime import datetime, timedelta, timezone # <-- [新增！] 用於設定過期時間
from app.core import email as email_service # <-- [新增！] 導入我們「假」的郵件服務
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound


# --- 導入我們所有的「零件」---

# 1. API 守門員 (Schemas)
from app.schemas import user as user_schemas 
# 2. 資料庫藍圖 (Models)
from app.models import user as user_models
# 3. 資料庫連線 (Session)
from db.session import get_db
# 4. 保全系統 (Security)
from app.core import security


# 建立一個 FastAPI "Router"，我們稍後會把它掛載到主 app 上
router = APIRouter()

@router.post(
    "/auth/signup", 
    response_model=user_schemas.UserPublic, # 守門員：定義回傳的格式
    status_code=status.HTTP_201_CREATED,     # 成功時回傳 201
    tags=["Authentication"]                  # API 文件分組
)
def signup(
    *,
    db: Session = Depends(get_db),
    user_in: user_schemas.UserCreate # 守門員：驗證傳入的 Body
):
    """
    新用戶註冊 API。
    - 驗證 email 格式 (by UserCreate)
    - 驗證密碼長度 (by UserCreate)
    - 檢查 email 是否已存在
    - 雜湊密碼並儲存
    - 建立對應的 Profile
    """
    
    # --- 業務邏輯：檢查 email 是否已存在 ---
    try:
        existing_user = db.query(user_models.User).filter(user_models.User.email == user_in.email).one()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered.",
            )
    except NoResultFound:
        pass # Email 可用，繼續執行

    # --- 核心邏輯：建立 User 和 Profile ---
    
    # 1. 建立 User model 物件
    new_user = user_models.User(
        email=user_in.email,
        # (注意) 我們在 user.py 中把 provider 拿掉了，
        # 如果你後來有加回來 (例如 UserProvider.PASSWORD)，記得在這裡加上
    )
    
    # 2. 呼叫我們在 User model 中建立的函式來設定密碼
    new_user.set_password(user_in.password)
    
    # 3. 建立 Profile model 物件
    new_profile = user_models.Profile(
        user=new_user, # 關鍵！將 profile 關聯到 user
        display_name=user_in.display_name or user_in.email.split('@')[0] # 提供一個預設暱稱
    )
    
    # 4. 將物件加入 session 並寫入資料庫
    db.add(new_user)
    db.add(new_profile)
    db.commit()
    db.refresh(new_user) # 重新整理，取得 DB 產生的 user_id
    
    # 5. 回傳 (Pydantic 會自動過濾，只回傳 UserPublic 定義的欄位)
    return new_user


@router.post(
    "/auth/login", 
    response_model=user_schemas.Token, # 守門員：回傳 Token 格式
    tags=["Authentication"]
)
def login(
    user_in: user_schemas.UserLogin, # 守門員：驗證傳入的 Body
    db: Session = Depends(get_db),
):
    """
    用戶登入 API。
    - 驗證 email 是否存在
    - 驗證密碼是否正確
    - 回傳 JWT Access Token
    """
    
    # --- 業務邏輯：驗證使用者 ---
    try:
        # 1. 找使用者
        user = db.query(user_models.User).filter(user_models.User.email == user_in.email).one()
    except NoResultFound:
        # (安全提示) 不要提示 "User not found"，統一回傳一樣的錯誤
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
        
    # 2. 驗證密碼 (使用我們在 User model 建立的函式)
    if not user.check_password(user_in.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    # --- 核心邏輯：產生 Token ---
    access_token = security.create_access_token(
        data={"sub": str(user.user_id)} # 'sub' (subject) 是 JWT 的標準 field，我們用它來存 user_id
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get(
    "/auth/me", 
    response_model=user_schemas.UserPublic, # 守門員：回傳安全的 UserPublic
    tags=["Authentication", "Profile"]
)
def get_me(
    # --- 核心邏輯：保全系統 ---
    # 這個 Depends(get_current_user) 就是「警衛」
    # 它會自動驗證 Token，如果失敗，連這行程式碼都不會執行到
    # 如果成功，它會把 User Model 物件放進 current_user 變數
    current_user: user_models.User = Depends(security.get_current_user)
):
    """
    取得當前登入用戶的資料 (用於 Profile 頁面)。
    這是一個受保護的端點，必須提供有效的 Access Token。
    """
    # 既然警衛已放行，我們直接回傳 current_user 即可
    # Pydantic (response_model) 會自動幫我們過濾掉 password_hash
    return current_user

# --- [新增！] (B) 更改密碼 API ---
@router.post(
    "/auth/change-password", 
    response_model=user_schemas.UserPublic, # (或者回傳一個 {"message": "Success"})
    tags=["Authentication"]
)
def change_password(
    password_in: user_schemas.PasswordChange, # 守門員
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(security.get_current_user) # 警衛
):
    """
    更改當前登入使用者的密碼。
    """
    
    # 1. 驗證「舊密碼」是否正確
    if not current_user.check_password(password_in.old_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password.",
        )
    
    # (可選) 檢查新舊密碼是否一樣
    if password_in.old_password == password_in.new_password:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the old password.",
        )

    # 2. 設定新密碼 (使用我們在 Model 中建立的函式)
    current_user.set_password(password_in.new_password)
    
    db.add(current_user)
    db.commit()
    
    # 3. (重要！) 回傳更新後的 User
    # (或者你可以簡單回傳 {"message": "Password updated successfully"})
    return current_user

# --- [新增！] (A) 忘記密碼 API ---
@router.post(
    "/auth/forgot-password", 
    tags=["Authentication"]
)
def forgot_password(
    request: user_schemas.ForgotPasswordRequest, # 守門員
    db: Session = Depends(get_db)
):
    """
    使用者請求密碼重設。
    1. 尋找 email。
    2. 產生一個有時效性的 token。
    3. 儲存 token。
    4. 發送「假的」Email (印在控制台)。
    """
    
    # 1. 尋找使用者
    try:
        user = db.query(user_models.User).filter(user_models.User.email == request.email).one()
    except NoResultFound:
        # [安全提示] 即使 email 不存在，我們也回傳 200 OK
        # 這樣攻擊者就無法利用這個 API 來探測哪些 email 是註冊過的
        print(f"密碼重設請求 (但 email 不存在): {request.email}")
        return {"message": "If your email is registered, you will receive a reset link shortly."}

    # 2. 產生一個安全的 token
    token = secrets.token_urlsafe(32)
    
    # 3. 設定過期時間 (例如：30 分鐘後)
    expiry_time = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    # 4. 將 token 和過期時間存入資料庫
    user.reset_token = token
    user.reset_token_expiry = expiry_time
    
    db.add(user)
    db.commit()
    
    # 5. 發送「假的」Email (會印在 Uvicorn 終端機)
    email_service.send_password_reset_email(email=user.email, token=token)

    return {"message": "If your email is registered, you will receive a reset link shortly."}

# ... (在 forgot_password 函式結束後) ...

# --- [新增！] (B) 重設密碼 API ---
@router.post(
    "/auth/reset-password", 
    response_model=user_schemas.UserPublic, # 成功後回傳用戶資料
    tags=["Authentication"]
)
def reset_password(
    request: user_schemas.ResetPasswordRequest, # 守門員
    db: Session = Depends(get_db)
):
    """
    使用者使用 Token 重設密碼。
    1. 驗證 Token。
    2. 檢查 Token 是否過期。
    3. 更新密碼。
    4. 清除 Token。
    """
    
    # 1. 驗證 Token 是否存在於資料庫
    try:
        user = db.query(user_models.User).filter(user_models.User.reset_token == request.token).one()
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )
        
    # 2. 檢查 Token 是否過期
    if not user.reset_token_expiry or user.reset_token_expiry < datetime.now(timezone.utc):
        # (安全起見，也清除過期的 token)
        user.reset_token = None
        user.reset_token_expiry = None
        db.add(user)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )
    
    # 3. Token 驗證成功！ 更新密碼
    user.set_password(request.new_password)
    
    # 4. [關鍵！] 清除 Token，使其「一次性」使用
    user.reset_token = None
    user.reset_token_expiry = None
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user