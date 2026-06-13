from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.settlement import Settlement
from app.schemas.settlement import SettlementCreate, SettlementOut
from app.services.currency import convert_to_inr

router = APIRouter(prefix="/settlements", tags=["Settlements"])


def _build_settlement_out(s: Settlement) -> dict:
    return {
        "id": s.id,
        "group_id": s.group_id,
        "payer_id": s.payer_id,
        "payer_name": s.payer.name,
        "payee_id": s.payee_id,
        "payee_name": s.payee.name,
        "amount": s.amount,
        "currency": s.currency,
        "amount_inr": s.amount_inr,
        "settled_at": s.settled_at,
        "notes": s.notes,
        "created_at": s.created_at,
    }


@router.post("/", response_model=SettlementOut, status_code=status.HTTP_201_CREATED)
def record_settlement(
    data: SettlementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Record that someone paid someone else.
    This reduces the payer's debt and the payee's credit in balance calculations.
    """
    if data.payer_id == data.payee_id:
        raise HTTPException(status_code=400, detail="Payer and payee cannot be the same person")

    try:
        amount_inr = convert_to_inr(data.amount, data.currency)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    settlement = Settlement(
        group_id=data.group_id,
        payer_id=data.payer_id,
        payee_id=data.payee_id,
        amount=data.amount,
        currency=data.currency,
        amount_inr=amount_inr,
        settled_at=data.settled_at or datetime.now(timezone.utc),
        notes=data.notes,
    )
    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    return _build_settlement_out(settlement)


@router.get("/group/{group_id}", response_model=List[SettlementOut])
def list_group_settlements(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all settlements for a group, newest first."""
    settlements = (
        db.query(Settlement)
        .filter(Settlement.group_id == group_id)
        .order_by(Settlement.settled_at.desc())
        .all()
    )
    return [_build_settlement_out(s) for s in settlements]
