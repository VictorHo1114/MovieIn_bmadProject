from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from db.database import get_db
from app.core.security import get_current_user
from app.models import Friendship, User
from app.schemas.friends import (
    FriendUser,
    FriendshipCreateBody,
    FriendshipRespondBody,
    FriendshipItem,
    FriendsListResponse,
    SuggestedFriendsResponse,
    SuggestedFriend,
    PendingRequest,
)

router = APIRouter(prefix="/api/v1/friends", tags=["friends"])


def _to_friend_user(user: User) -> FriendUser:
    profile = getattr(user, "profile", None)
    display = None
    avatar = None
    if profile is not None:
        display = getattr(profile, "display_name", None)
        avatar = getattr(profile, "avatar_url", None)
    # fallback to email local-part
    if not display and getattr(user, "email", None):
        display = user.email.split("@")[0]
    return FriendUser(user_id=user.user_id, display_name=display, avatar_url=avatar)


@router.get("", response_model=FriendsListResponse)
def list_friends(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """取得目前使用者的好友清單（accepted）"""
    rels = (
        db.query(Friendship)
        .filter(
            ((Friendship.user_id == current_user.user_id) | (Friendship.friend_id == current_user.user_id)),
            Friendship.status == "accepted",
        )
        .all()
    )

    items: List[FriendUser] = []
    for r in rels:
        other_id = r.friend_id if r.user_id == current_user.user_id else r.user_id
        user = db.query(User).filter(User.user_id == other_id).first()
        if user:
            items.append(_to_friend_user(user))

    return FriendsListResponse(items=items, total=len(items))


@router.get("/suggested", response_model=SuggestedFriendsResponse)
def suggested_friends(limit: int = 12, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """簡單的建議好友：挑選未與使用者有關聯的最近註冊使用者"""
    # 收集要排除的 user ids（自己 + 已有的 friendships）
    excludes = {current_user.user_id}
    rels = (
        db.query(Friendship)
        .filter((Friendship.user_id == current_user.user_id) | (Friendship.friend_id == current_user.user_id))
        .all()
    )
    for r in rels:
        excludes.add(r.user_id)
        excludes.add(r.friend_id)

    q = db.query(User).filter(~User.user_id.in_(list(excludes))).limit(limit).all()

    items: List[SuggestedFriend] = []
    for u in q:
        profile = getattr(u, "profile", None)
        display = None
        avatar = None
        if profile is not None:
            display = getattr(profile, "display_name", None)
            avatar = getattr(profile, "avatar_url", None)
        if not display and getattr(u, "email", None):
            display = u.email.split("@")[0]
        items.append(SuggestedFriend(user_id=u.user_id, display_name=display, avatar_url=avatar))

    return SuggestedFriendsResponse(items=items, total=len(items))


@router.get("/requests", response_model=List[PendingRequest])
def incoming_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """列出目前使用者收到的好友邀請（status == pending，friend_id == current_user），並附帶發送者的顯示名稱與頭像"""
    rows = (
        db.query(Friendship)
        .filter(Friendship.friend_id == current_user.user_id, Friendship.status == "pending")
        .order_by(Friendship.created_at.desc())
        .all()
    )
    items: List[PendingRequest] = []
    for f in rows:
        # 取得發送者資訊
        sender = db.query(User).filter(User.user_id == f.user_id).first()
        display = None
        avatar = None
        if sender and getattr(sender, "profile", None):
            display = getattr(sender.profile, "display_name", None)
            avatar = getattr(sender.profile, "avatar_url", None)
        if not display and sender and getattr(sender, "email", None):
            display = sender.email.split("@")[0]

        items.append(
            PendingRequest(
                id=f.id,
                user_id=f.user_id,
                friend_id=f.friend_id,
                display_name=display,
                avatar_url=avatar,
                message=f.message,
                created_at=f.created_at,
            )
        )
    return items


@router.get("/requests/sent", response_model=List[PendingRequest])
def outgoing_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """列出目前使用者發出的好友邀請（status == pending，user_id == current_user），並附帶被邀請者的基本資訊"""
    rows = (
        db.query(Friendship)
        .filter(Friendship.user_id == current_user.user_id, Friendship.status == "pending")
        .order_by(Friendship.created_at.desc())
        .all()
    )
    items: List[PendingRequest] = []
    for f in rows:
        receiver = db.query(User).filter(User.user_id == f.friend_id).first()
        display = None
        avatar = None
        if receiver and getattr(receiver, "profile", None):
            display = getattr(receiver.profile, "display_name", None)
            avatar = getattr(receiver.profile, "avatar_url", None)
        if not display and receiver and getattr(receiver, "email", None):
            display = receiver.email.split("@")[0]

        items.append(
            PendingRequest(
                id=f.id,
                user_id=f.user_id,
                friend_id=f.friend_id,
                display_name=display,
                avatar_url=avatar,
                message=f.message,
                created_at=f.created_at,
            )
        )
    return items


@router.get("/requests/count")
def incoming_requests_count(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """回傳目前使用者收到的待處理好友邀請數量（只回傳數字）"""
    count = (
        db.query(Friendship)
        .filter(Friendship.friend_id == current_user.user_id, Friendship.status == "pending")
        .count()
    )
    return {"count": count}



@router.delete("/{friend_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_friend(friend_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """移除好友關係（unfriend）。會搜尋目前使用者與 friend_id 之間的 accepted friendship，並刪除該紀錄。
    如果找不到已接受的 friendship，回傳 404。"""
    f = (
        db.query(Friendship)
        .filter(
            (
                (Friendship.user_id == current_user.user_id) & (Friendship.friend_id == friend_id)
            )
            | (
                (Friendship.user_id == friend_id) & (Friendship.friend_id == current_user.user_id)
            )
        )
        .filter(Friendship.status == "accepted")
        .first()
    )

    if not f:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accepted friendship not found")

    # Only participants can delete; double check
    if current_user.user_id not in (f.user_id, f.friend_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this friendship")

    # Soft-delete: 標記為 deleted 並紀錄時間，以便允許 undo
    f.status = "deleted"
    f.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(f)
    return None


@router.post("/{friend_id}/restore", response_model=FriendshipItem)
def restore_friend(friend_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """恢復已被移除（status == 'deleted'）的 friendship（undo）。只允許關係參與者執行，且需為 deleted 狀態。"""
    f = (
        db.query(Friendship)
        .filter(
            (
                (Friendship.user_id == current_user.user_id) & (Friendship.friend_id == friend_id)
            )
            | (
                (Friendship.user_id == friend_id) & (Friendship.friend_id == current_user.user_id)
            )
        )
        .filter(Friendship.status == "deleted")
        .first()
    )

    if not f:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deleted friendship not found")

    if current_user.user_id not in (f.user_id, f.friend_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to restore this friendship")

    f.status = "accepted"
    f.deleted_at = None
    db.commit()
    db.refresh(f)
    return FriendshipItem(
        id=f.id,
        user_id=f.user_id,
        friend_id=f.friend_id,
        status=f.status,
        created_at=f.created_at,
        accepted_at=f.accepted_at,
        message=f.message,
    )


@router.delete("/requests/{friendship_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_sent_request(friendship_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """取消已發出的好友邀請（pending）。只允許邀請發送者刪除。實作為直接刪除 pending row。"""
    f = db.query(Friendship).filter(Friendship.id == friendship_id).first()
    if not f:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friendship not found")
    if f.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to cancel this request")
    if f.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Friendship is not pending")

    db.delete(f)
    db.commit()
    return None


@router.post("/requests/{friendship_id}/accept", response_model=FriendshipItem)
def accept_request(friendship_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    f = db.query(Friendship).filter(Friendship.id == friendship_id).first()
    if not f:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friendship not found")
    if f.friend_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to accept this request")
    if f.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Friendship is not pending")
    f.status = "accepted"
    from datetime import datetime
    f.accepted_at = datetime.utcnow()
    db.commit()
    db.refresh(f)
    return FriendshipItem(
        id=f.id,
        user_id=f.user_id,
        friend_id=f.friend_id,
        status=f.status,
        created_at=f.created_at,
        accepted_at=f.accepted_at,
        message=f.message,
    )


@router.post("/requests/{friendship_id}/ignore", response_model=FriendshipItem)
def ignore_request(friendship_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    f = db.query(Friendship).filter(Friendship.id == friendship_id).first()
    if not f:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friendship not found")
    if f.friend_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to ignore this request")
    if f.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Friendship is not pending")
    f.status = "rejected"
    db.commit()
    db.refresh(f)
    return FriendshipItem(
        id=f.id,
        user_id=f.user_id,
        friend_id=f.friend_id,
        status=f.status,
        created_at=f.created_at,
        accepted_at=f.accepted_at,
        message=f.message,
    )


@router.post("/request", response_model=FriendshipItem, status_code=status.HTTP_201_CREATED)
def send_friend_request(body: FriendshipCreateBody, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """送出好友邀請（建立 friendship，狀態 pending）"""
    if body.friend_id == current_user.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot friend yourself")

    # 檢查對方是否存在
    other = db.query(User).filter(User.user_id == body.friend_id).first()
    if not other:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")

    # 檢查是否已存在 friendship（任一方向）
    existing = (
        db.query(Friendship)
        .filter(
            ((Friendship.user_id == current_user.user_id) & (Friendship.friend_id == body.friend_id))
            | ((Friendship.user_id == body.friend_id) & (Friendship.friend_id == current_user.user_id))
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Friendship already exists")

    f = Friendship(user_id=current_user.user_id, friend_id=body.friend_id, status="pending", message=body.message)
    db.add(f)
    db.commit()
    db.refresh(f)

    return FriendshipItem(
        id=f.id,
        user_id=f.user_id,
        friend_id=f.friend_id,
        status=f.status,
        created_at=f.created_at,
        accepted_at=f.accepted_at,
        message=f.message,
    )


@router.post("/respond", response_model=FriendshipItem)
def respond_friend_request(body: FriendshipRespondBody, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """回應好友邀請：接受 / 拒絕 / 封鎖"""
    f = db.query(Friendship).filter(Friendship.id == body.friendship_id).first()
    if not f:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friendship not found")

    # 只有被邀請者 (friend_id) 可以回應
    if f.friend_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to respond to this request")

    action = body.action.lower()
    now = datetime.utcnow()
    if action == "accept":
        f.status = "accepted"
        f.accepted_at = now
    elif action == "reject":
        f.status = "rejected"
    elif action == "block":
        f.status = "blocked"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action")

    db.commit()
    db.refresh(f)

    return FriendshipItem(
        id=f.id,
        user_id=f.user_id,
        friend_id=f.friend_id,
        status=f.status,
        created_at=f.created_at,
        accepted_at=f.accepted_at,
        message=f.message,
    )
