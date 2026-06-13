from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.schemas.user import UserOut


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class GroupMemberOut(BaseModel):
    id: int
    user: UserOut
    joined_at: datetime
    left_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GroupOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_by_id: int
    created_at: datetime
    members: List[GroupMemberOut] = []

    class Config:
        from_attributes = True


class AddMemberRequest(BaseModel):
    user_id: int
    joined_at: Optional[datetime] = None  # Defaults to now if not provided


class RemoveMemberRequest(BaseModel):
    user_id: int
    left_at: Optional[datetime] = None  # Defaults to now if not provided
