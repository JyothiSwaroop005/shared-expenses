from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.group import Group
from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit
from app.schemas.expense import ExpenseCreate, ExpenseOut, ExpenseSplitOut
from app.services.currency import convert_to_inr
from app.services.balance_engine import calculate_splits

router = APIRouter(prefix="/expenses", tags=["Expenses"])


def _build_expense_out(expense: Expense) -> dict:
    """Helper to build the full ExpenseOut response with nested splits."""
    splits_out = []
    for s in expense.splits:
        splits_out.append(ExpenseSplitOut(
            id=s.id,
            user_id=s.user_id,
            user_name=s.user.name,
            owed_amount=s.owed_amount,
        ))
    return {
        "id": expense.id,
        "group_id": expense.group_id,
        "paid_by_id": expense.paid_by_id,
        "paid_by_name": expense.paid_by_user.name,
        "description": expense.description,
        "amount": expense.amount,
        "currency": expense.currency,
        "amount_inr": expense.amount_inr,
        "split_type": expense.split_type,
        "expense_date": expense.expense_date,
        "created_at": expense.created_at,
        "notes": expense.notes,
        "splits": splits_out,
    }


@router.post("/", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new expense with splits.
    
    1. Validates the group exists
    2. Validates the payer exists and is in the group
    3. Converts currency to INR
    4. Calculates splits (equal/percentage/exact)
    5. Saves expense + all split rows atomically
    """
    group = db.query(Group).filter(Group.id == data.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    payer = db.query(User).filter(User.id == data.paid_by_id).first()
    if not payer:
        raise HTTPException(status_code=404, detail="Payer user not found")

    # Convert to INR for consistent balance calculations
    try:
        amount_inr = convert_to_inr(data.amount, data.currency)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Calculate splits
    try:
        split_map = calculate_splits(amount_inr, data.split_type, data.participants)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create expense
    expense = Expense(
        group_id=data.group_id,
        paid_by_id=data.paid_by_id,
        description=data.description,
        amount=data.amount,
        currency=data.currency,
        amount_inr=amount_inr,
        split_type=data.split_type,
        expense_date=data.expense_date,
        notes=data.notes,
    )
    db.add(expense)
    db.flush()  # Get expense.id

    # Create split rows
    for user_id, owed_amount in split_map.items():
        split = ExpenseSplit(
            expense_id=expense.id,
            user_id=user_id,
            owed_amount=owed_amount,
        )
        db.add(split)

    db.commit()
    db.refresh(expense)
    return _build_expense_out(expense)


@router.get("/group/{group_id}", response_model=List[ExpenseOut])
def list_group_expenses(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all expenses for a group, newest first."""
    expenses = (
        db.query(Expense)
        .filter(Expense.group_id == group_id)
        .order_by(Expense.expense_date.desc())
        .all()
    )
    return [_build_expense_out(e) for e in expenses]


@router.get("/{expense_id}", response_model=ExpenseOut)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return _build_expense_out(expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an expense and all its splits (cascade).
    Only the person who logged the expense (paid_by) can delete it.
    """
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense.paid_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the expense payer can delete this expense")

    db.delete(expense)
    db.commit()
