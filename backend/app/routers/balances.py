from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from decimal import Decimal

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.group import Group
from app.services.balance_engine import get_group_balances, simplify_debts

router = APIRouter(prefix="/balances", tags=["Balances"])


@router.get("/group/{group_id}")
def get_balances(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return two things:
    1. raw_balances: {user_id: net_balance} - positive = owed, negative = owes
    2. simplified: the minimum transactions to settle all debts (Aisha's view)
    
    Also returns user names so the frontend doesn't need another API call.
    """
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    raw_balances = get_group_balances(group_id, db)
    simplified = simplify_debts(raw_balances)

    # Enrich with user names for the frontend
    all_user_ids = set(raw_balances.keys())
    for t in simplified:
        all_user_ids.add(t["from_user_id"])
        all_user_ids.add(t["to_user_id"])

    users = db.query(User).filter(User.id.in_(all_user_ids)).all()
    user_map = {u.id: u.name for u in users}

    raw_with_names = [
        {
            "user_id": uid,
            "user_name": user_map.get(uid, f"User {uid}"),
            "balance": float(balance),
            "status": "owed" if balance > 0 else ("owes" if balance < 0 else "settled"),
        }
        for uid, balance in raw_balances.items()
    ]

    simplified_with_names = [
        {
            "from_user_id": t["from_user_id"],
            "from_user_name": user_map.get(t["from_user_id"], f"User {t['from_user_id']}"),
            "to_user_id": t["to_user_id"],
            "to_user_name": user_map.get(t["to_user_id"], f"User {t['to_user_id']}"),
            "amount": float(t["amount"]),
        }
        for t in simplified
    ]

    return {
        "group_id": group_id,
        "group_name": group.name,
        "raw_balances": raw_with_names,
        "simplified_transactions": simplified_with_names,
    }


@router.get("/user/summary")
def get_my_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a summary of what the current user owes and is owed across ALL groups.
    This is the personal dashboard view.
    """
    from app.models.group_member import GroupMember
    from app.models.group import Group

    # Find all groups this user is (or was) in
    memberships = db.query(GroupMember).filter(
        GroupMember.user_id == current_user.id
    ).all()

    total_owed_to_me = Decimal("0")   # Others owe me this
    total_i_owe = Decimal("0")        # I owe others this
    group_summaries = []

    for m in memberships:
        group = db.query(Group).filter(Group.id == m.group_id).first()
        if not group:
            continue

        balances = get_group_balances(m.group_id, db)
        my_balance = balances.get(current_user.id, Decimal("0"))

        if my_balance > 0:
            total_owed_to_me += my_balance
        else:
            total_i_owe += abs(my_balance)

        group_summaries.append({
            "group_id": m.group_id,
            "group_name": group.name,
            "my_balance": float(my_balance),
            "status": "owed" if my_balance > 0 else ("owes" if my_balance < 0 else "settled"),
        })

    return {
        "user_id": current_user.id,
        "user_name": current_user.name,
        "total_owed_to_me": float(total_owed_to_me),
        "total_i_owe": float(total_i_owe),
        "net": float(total_owed_to_me - total_i_owe),
        "groups": group_summaries,
    }
