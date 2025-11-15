# 檔案：backend/app/routers/profile.py (新檔案)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.schemas import user as user_schemas
from app.models import user as user_models
from db.database import get_db
from app.core.security import get_current_user

router = APIRouter()

@router.patch(
    "/profile/me", 
    response_model=user_schemas.UserPublic, # 更新完後，回傳最新的 User
    tags=["Profile"]
)
def update_my_profile(
    profile_in: user_schemas.ProfileUpdate, # 守門員：驗證傳入的 Body
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_user) # 警衛
):
    """
    更新當前登入使用者的 Profile。
    (目前只支援更新 display_name)
    """
    
    # 1. 取得當前用戶的 Profile (它一定存在)
    profile = current_user.profile
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found for this user.")

    # 2. 取得傳入的資料 (Pydantic 會自動過濾掉 'unset' 的欄位)
    update_data = profile_in.model_dump(exclude_unset=True)

    # 3. 迭代並更新欄位 (這樣我們未來就可以輕易擴充)
    for field, value in update_data.items():
        if value is not None:
            setattr(profile, field, value)
    
    db.add(profile)
    db.commit()
    db.refresh(current_user) # 重新整理 'current_user' (它關聯的 profile 變了)
    
    return current_user



@router.get(
    "/profile/{user_id}",
    response_model=user_schemas.UserPublic,
    tags=["Profile"]
)
def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    """取得任一使用者的公開資料（包含 profile）。

    這個 endpoint 接受字串形式的 user_id（例如 UUID 字串），並會嘗試轉換。
    若轉換失敗或查無使用者，會回傳 404 或 400。
    """
    # 嘗試解析為 UUID（容錯），若失敗仍然嘗試以原始字串查詢
    try:
        from uuid import UUID as _UUID

        parsed = _UUID(user_id)
    except Exception:
        parsed = None

    if parsed is not None:
        user = db.query(user_models.User).filter(user_models.User.user_id == parsed).first()
    else:
        # fallback: try matching by string (some deployments may store as text)
        user = db.query(user_models.User).filter(user_models.User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user