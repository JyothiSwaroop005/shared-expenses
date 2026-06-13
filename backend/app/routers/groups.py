from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.group import Group
from app.models.group_member import GroupMember
from app.schemas.group import GroupCreate, GroupUpdate, GroupOut, AddMemberRequest, RemoveMemberRequest

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.post("/", response_model=GroupOut, status_code=status.HTTP_201_CREATED)
def create_group(
    data: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new group. The creator is automatically added as the first member.
    """
    group = Group(
        name=data.name,
        description=data.description,
        created_by_id=current_user.id,
    )
    db.add(group)
    db.flush()

    # Auto-add creator as first member
    membership = GroupMember(
        group_id=group.id,
        user_id=current_user.id,
        joined_at=datetime.now(timezone.utc),
    )
    db.add(membership)
    db.commit()
    db.refresh(group)
    return group


@router.get("/", response_model=List[GroupOut])
def list_my_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all groups the current user is (or was) a member of."""
    memberships = (
        db.query(GroupMember)
        .filter(GroupMember.user_id == current_user.id)
        .all()
    )
    group_ids = [m.group_id for m in memberships]
    return db.query(Group).filter(Group.id.in_(group_ids)).all()


@router.get("/{group_id}", response_model=GroupOut)
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.patch("/{group_id}", response_model=GroupOut)
def update_group(
    group_id: int,
    data: GroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if group.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the group creator can edit it")

    if data.name is not None:
        group.name = data.name
    if data.description is not None:
        group.description = data.description

    db.commit()
    db.refresh(group)
    return group


@router.post("/{group_id}/members", response_model=GroupOut)
def add_member(
    group_id: int,
    data: AddMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add a user to a group.
    joined_at defaults to now if not provided.
    Allows backdating (e.g., "Rohan joined on Jan 1").
    """
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if already an active member
    existing = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == data.user_id,
        GroupMember.left_at == None,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this group")

    joined_at = data.joined_at or datetime.now(timezone.utc)
    membership = GroupMember(
        group_id=group_id,
        user_id=data.user_id,
        joined_at=joined_at,
    )
    db.add(membership)
    db.commit()
    db.refresh(group)
    return group


@router.delete("/{group_id}/members/{user_id}", response_model=GroupOut)
def remove_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark a user as having left the group (sets left_at = now).
    We do NOT delete the membership row - we need the history.
    """
    membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
        GroupMember.left_at == None,
    ).first()

    if not membership:
        raise HTTPException(status_code=404, detail="Active membership not found")

    membership.left_at = datetime.now(timezone.utc)
    db.commit()

    group = db.query(Group).filter(Group.id == group_id).first()
    return group
