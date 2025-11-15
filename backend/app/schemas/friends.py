from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class FriendUser(BaseModel):
    user_id: UUID
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class FriendshipCreateBody(BaseModel):
    friend_id: UUID
    message: Optional[str] = None


class FriendshipRespondBody(BaseModel):
    friendship_id: UUID
    action: str  # accept | reject | block


class FriendshipItem(BaseModel):
    id: UUID
    user_id: UUID
    friend_id: UUID
    status: str
    created_at: Optional[datetime]
    accepted_at: Optional[datetime] = None
    message: Optional[str] = None


class PendingRequest(BaseModel):
    id: UUID
    user_id: UUID
    friend_id: UUID
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    message: Optional[str] = None
    created_at: Optional[datetime]


class FriendsListResponse(BaseModel):
    items: List[FriendUser]
    total: int


class SuggestedFriend(BaseModel):
    user_id: UUID
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class SuggestedFriendsResponse(BaseModel):
    items: List[SuggestedFriend]
    total: int
