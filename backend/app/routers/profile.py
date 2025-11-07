# 檔案：backend/app/routers/profile.py (新檔案)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas import user as user_schemas
from app.models import user as user_models
from db.session import get_db
from app.core import security

router = APIRouter()

@router.patch(
    "/profile/me", 
    response_model=user_schemas.UserPublic, # 更新完後，回傳最新的 User
    tags=["Profile"]
)
def update_my_profile(
    profile_in: user_schemas.ProfileUpdate, # 守門員：驗證傳入的 Body
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(security.get_current_user) # 警衛
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