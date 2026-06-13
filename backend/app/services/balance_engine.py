from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Dict
from app.models.expense import Expense, SplitType
from app.models.expense_split import ExpenseSplit
from app.models.settlement import Settlement
from app.models.group_member import GroupMember


def calculate_splits(
    amount_inr: Decimal,
    split_type: str,
    participants: list,
) -> Dict[int, Decimal]:
    """
    Given a total amount and participants, return a dict of {user_id: owed_amount}.
    
    EQUAL SPLIT:
    - Each person owes amount / num_people
    - Remainder (from rounding) goes to the first person
    - Example: ₹100 split 3 ways = ₹33.34, ₹33.33, ₹33.33
    
    PERCENTAGE SPLIT:
    - Each participant has a 'value' field (0-100) representing their share %
    - Example: Aisha=50%, Rohan=30%, Priya=20% of ₹1000
    - Result: Aisha=₹500, Rohan=₹300, Priya=₹200
    
    EXACT SPLIT:
    - Each participant has a 'value' field with their exact amount
    - Example: Aisha=₹400, Rohan=₹350, Priya=₹250
    - Validation: sum of exact amounts must equal total
    """
    result = {}

    if split_type == SplitType.EQUAL or split_type == "equal":
        n = len(participants)
        if n == 0:
            return {}
        # Integer division to get base share
        base_share = (amount_inr / n).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_assigned = base_share * n
        # Remainder from rounding
        remainder = amount_inr - total_assigned

        for i, p in enumerate(participants):
            uid = p.user_id if hasattr(p, "user_id") else p["user_id"]
            share = base_share
            if i == 0:  # First person absorbs the rounding remainder
                share = base_share + remainder
            result[uid] = share

    elif split_type == SplitType.PERCENTAGE or split_type == "percentage":
        total_pct = sum(
            Decimal(str(p.value if hasattr(p, "value") else p["value"])) for p in participants
        )
        if abs(total_pct - Decimal("100")) > Decimal("0.01"):
            raise ValueError(f"Percentages must sum to 100, got {total_pct}")
        for p in participants:
            uid = p.user_id if hasattr(p, "user_id") else p["user_id"]
            pct = Decimal(str(p.value if hasattr(p, "value") else p["value"]))
            result[uid] = (amount_inr * pct / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

    elif split_type == SplitType.EXACT or split_type == "exact":
        total_exact = sum(
            Decimal(str(p.value if hasattr(p, "value") else p["value"])) for p in participants
        )
        if abs(total_exact - amount_inr) > Decimal("0.01"):
            raise ValueError(
                f"Exact amounts ({total_exact}) must sum to total ({amount_inr})"
            )
        for p in participants:
            uid = p.user_id if hasattr(p, "user_id") else p["user_id"]
            result[uid] = Decimal(str(p.value if hasattr(p, "value") else p["value"]))

    return result


def get_group_balances(group_id: int, db: Session) -> Dict[int, Decimal]:
    """
    Calculate the net balance for every user in a group.
    
    Algorithm:
    1. For each expense: the payer is owed (+amount_inr) from others
    2. For each split: the participant owes (-owed_amount)
    3. For each settlement: payer reduces debt, payee reduces credit
    
    Positive balance = this person is owed money (net creditor)
    Negative balance = this person owes money (net debtor)
    
    Sam's requirement: only count expenses AFTER the user's join_at date.
    If user left, only count expenses BEFORE their left_at date.
    """
    balances: Dict[int, Decimal] = {}

    # Get all expenses for this group
    expenses = db.query(Expense).filter(Expense.group_id == group_id).all()

    for expense in expenses:
        # Step 1: The payer is owed the full expense amount
        payer_id = expense.paid_by_id
        if payer_id not in balances:
            balances[payer_id] = Decimal("0")
        balances[payer_id] += expense.amount_inr

        # Step 2: Each split participant owes their share
        for split in expense.splits:
            uid = split.user_id

            # Sam's requirement: check if this user was a member when expense occurred
            membership = (
                db.query(GroupMember)
                .filter(
                    and_(
                        GroupMember.group_id == group_id,
                        GroupMember.user_id == uid,
                        GroupMember.joined_at <= expense.expense_date,
                    )
                )
                .filter(
                    # Either still a member (left_at is NULL) or left after this expense
                    (GroupMember.left_at == None) | (GroupMember.left_at >= expense.expense_date)
                )
                .first()
            )

            if membership is None:
                # User was not a member at this time - skip their split
                continue

            if uid not in balances:
                balances[uid] = Decimal("0")
            balances[uid] -= split.owed_amount

    # Step 3: Apply settlements
    settlements = db.query(Settlement).filter(Settlement.group_id == group_id).all()
    for s in settlements:
        if s.payer_id not in balances:
            balances[s.payer_id] = Decimal("0")
        if s.payee_id not in balances:
            balances[s.payee_id] = Decimal("0")
        # Payer has paid off some debt (balance goes up)
        balances[s.payer_id] += s.amount_inr
        # Payee has received money (balance goes down - they're owed less)
        balances[s.payee_id] -= s.amount_inr

    return balances


def simplify_debts(balances: Dict[int, Decimal]) -> List[Dict]:
    """
    Aisha's requirement: "I just want one number per person. Who pays whom?"
    
    Convert a net balance map into the minimum set of transactions needed.
    
    Algorithm (Greedy debt simplification):
    1. Separate everyone into creditors (balance > 0) and debtors (balance < 0)
    2. Match the largest debtor with the largest creditor
    3. The debtor pays the minimum of (what they owe, what the creditor is owed)
    4. Repeat until all balances are zero
    
    Example:
    Aisha: +500, Rohan: -300, Priya: -200
    → Rohan pays Aisha ₹300
    → Priya pays Aisha ₹200
    Total: 2 transactions (vs potentially many more without simplification)
    """
    # Round tiny floating point errors to zero
    clean = {uid: b.quantize(Decimal("0.01")) for uid, b in balances.items() if abs(b) > Decimal("0.01")}

    creditors = sorted(
        [(uid, b) for uid, b in clean.items() if b > 0], key=lambda x: -x[1]
    )
    debtors = sorted(
        [(uid, -b) for uid, b in clean.items() if b < 0], key=lambda x: -x[1]
    )

    transactions = []
    ci, di = 0, 0

    while ci < len(creditors) and di < len(debtors):
        c_uid, c_amount = creditors[ci]
        d_uid, d_amount = debtors[di]

        payment = min(c_amount, d_amount)
        transactions.append({
            "from_user_id": d_uid,
            "to_user_id": c_uid,
            "amount": payment,
        })

        creditors[ci] = (c_uid, c_amount - payment)
        debtors[di] = (d_uid, d_amount - payment)

        if creditors[ci][1] <= Decimal("0.01"):
            ci += 1
        if debtors[di][1] <= Decimal("0.01"):
            di += 1

    return transactions
