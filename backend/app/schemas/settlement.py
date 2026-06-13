from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional
from decimal import Decimal


class SettlementCreate(BaseModel):
    group_id: int
    payer_id: int
    payee_id: int
    amount: Decimal
    currency: str = "INR"
    settled_at: Optional[datetime] = None
    notes: Optional[str] = None

    @validator("amount")
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Settlement amount must be greater than zero")
        return v

    @validator("payer_id")
    def payer_and_payee_must_differ(cls, v, values):
        if "payee_id" in values and v == values["payee_id"]:
            raise ValueError("Payer and payee cannot be the same person")
        return v


class SettlementOut(BaseModel):
    id: int
    group_id: int
    payer_id: int
    payer_name: str
    payee_id: int
    payee_name: str
    amount: Decimal
    currency: str
    amount_inr: Decimal
    settled_at: datetime
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
