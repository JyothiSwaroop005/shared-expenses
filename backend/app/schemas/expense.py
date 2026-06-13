from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from app.models.expense import SplitType


class SplitInput(BaseModel):
    user_id: int
    # For exact split: the amount. For percentage split: the percentage (0-100).
    # For equal split: this field is ignored.
    value: Optional[Decimal] = None


class ExpenseCreate(BaseModel):
    group_id: int
    paid_by_id: int
    description: str
    amount: Decimal
    currency: str = "INR"
    split_type: SplitType = SplitType.EQUAL
    expense_date: datetime
    notes: Optional[str] = None
    # For equal split: list of user_ids. For others: list of SplitInput with values.
    participants: List[SplitInput]

    @validator("amount")
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v

    @validator("currency")
    def currency_must_be_valid(cls, v):
        allowed = {"INR", "USD"}
        if v.upper() not in allowed:
            raise ValueError(f"Currency must be one of {allowed}")
        return v.upper()


class ExpenseSplitOut(BaseModel):
    id: int
    user_id: int
    user_name: str
    owed_amount: Decimal

    class Config:
        from_attributes = True


class ExpenseOut(BaseModel):
    id: int
    group_id: int
    paid_by_id: int
    paid_by_name: str
    description: str
    amount: Decimal
    currency: str
    amount_inr: Decimal
    split_type: SplitType
    expense_date: datetime
    created_at: datetime
    notes: Optional[str] = None
    splits: List[ExpenseSplitOut] = []

    class Config:
        from_attributes = True
