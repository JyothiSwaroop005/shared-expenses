import pandas as pd
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.group import Group
from app.models.group_member import GroupMember
from app.models.expense import Expense, SplitType
from app.models.expense_split import ExpenseSplit
from app.models.import_session import ImportSession
from app.models.import_anomaly import ImportAnomaly
from app.services.currency import convert_to_inr, SUPPORTED_CURRENCIES
from app.services.balance_engine import calculate_splits

# These are the exact column names we expect in the CSV
REQUIRED_COLUMNS = {
    "description", "amount", "currency", "paid_by",
    "group_name", "split_type", "expense_date"
}

# Anomaly type constants - use strings so they're searchable in the DB
ANOMALY_MISSING_COLUMN = "missing_required_column"
ANOMALY_MISSING_PAYER = "missing_payer"
ANOMALY_PAYER_NOT_IN_GROUP = "payer_not_in_group"
ANOMALY_INVALID_AMOUNT = "invalid_amount"
ANOMALY_NEGATIVE_AMOUNT = "negative_amount"
ANOMALY_ZERO_AMOUNT = "zero_amount"
ANOMALY_FUTURE_DATE = "future_date"
ANOMALY_INVALID_DATE = "invalid_date"
ANOMALY_INVALID_CURRENCY = "invalid_currency"
ANOMALY_UNKNOWN_SPLIT_TYPE = "unknown_split_type"
ANOMALY_GROUP_NOT_FOUND = "group_not_found"
ANOMALY_USER_NOT_FOUND = "user_not_found"
ANOMALY_PARTICIPANT_NOT_IN_GROUP = "participant_not_in_group"
ANOMALY_PERCENTAGE_NOT_100 = "percentage_sum_not_100"
ANOMALY_EXACT_SUM_MISMATCH = "exact_sum_mismatch"
ANOMALY_DUPLICATE_EXPENSE = "duplicate_expense"
ANOMALY_SETTLEMENT_AS_EXPENSE = "settlement_as_expense"
ANOMALY_MISSING_PARTICIPANTS = "missing_participants"


def run_import(
    file_bytes: bytes,
    filename: str,
    uploaded_by_id: int,
    db: Session,
) -> ImportSession:
    """
    Main entry point for CSV import.
    
    Flow:
    1. Create an ImportSession to track this upload
    2. Parse the CSV with pandas
    3. Check that required columns exist
    4. For each row: detect anomalies, then import or flag
    5. Update session counters
    6. Return the session (caller can query anomalies via session.id)
    
    NEVER raises an exception from bad data - all errors become anomalies.
    """
    session = ImportSession(
        filename=filename,
        uploaded_by_id=uploaded_by_id,
        status="pending",
    )
    db.add(session)
    db.flush()  # Flush to get session.id without committing

    try:
        df = pd.read_csv(pd.io.common.BytesIO(file_bytes))
    except Exception as e:
        session.status = "failed"
        db.commit()
        raise ValueError(f"Could not parse CSV file: {e}")

    # Normalize column names: strip whitespace, lowercase
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Check for missing required columns
    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        _log_anomaly(
            db, session.id, 0,
            ANOMALY_MISSING_COLUMN,
            f"CSV is missing required columns: {missing_cols}",
            {},
            "skipped",
        )
        session.status = "failed"
        session.total_rows = len(df)
        session.anomaly_count = 1
        db.commit()
        return session

    session.total_rows = len(df)
    imported = 0
    skipped = 0
    anomaly_count = 0

    for idx, row in df.iterrows():
        row_num = idx + 2  # +2 because idx is 0-based and row 1 is the header
        raw = row.to_dict()
        anomalies_this_row: List[Tuple[str, str]] = []

        # ── 1. Validate and parse each field ──────────────────────────────────

        # DESCRIPTION
        description = str(raw.get("description", "")).strip()
        if not description or description.lower() == "nan":
            description = "Untitled Expense"

        # AMOUNT
        raw_amount = raw.get("amount", "")
        amount = None
        try:
            amount = Decimal(str(raw_amount)).quantize(Decimal("0.01"))
            if amount < 0:
                anomalies_this_row.append((ANOMALY_NEGATIVE_AMOUNT, f"Amount is negative: {amount}"))
            elif amount == 0:
                anomalies_this_row.append((ANOMALY_ZERO_AMOUNT, f"Amount is zero"))
        except (InvalidOperation, ValueError):
            anomalies_this_row.append((ANOMALY_INVALID_AMOUNT, f"Cannot parse amount: '{raw_amount}'"))

        # CURRENCY
        currency = str(raw.get("currency", "INR")).strip().upper()
        if currency not in SUPPORTED_CURRENCIES:
            anomalies_this_row.append((ANOMALY_INVALID_CURRENCY, f"Unknown currency: '{currency}'. Defaulting to INR."))
            currency = "INR"

        # EXPENSE DATE
        raw_date = raw.get("expense_date", "")
        expense_date = None
        try:
            expense_date = pd.to_datetime(raw_date, dayfirst=False)
            expense_date = expense_date.to_pydatetime().replace(tzinfo=timezone.utc)
            if expense_date > datetime.now(timezone.utc):
                anomalies_this_row.append((ANOMALY_FUTURE_DATE, f"Expense date is in the future: {raw_date}"))
        except Exception:
            anomalies_this_row.append((ANOMALY_INVALID_DATE, f"Cannot parse date: '{raw_date}'"))

        # SPLIT TYPE
        raw_split = str(raw.get("split_type", "equal")).strip().lower()
        split_type = None
        if raw_split in ("equal", "percentage", "exact"):
            split_type = SplitType(raw_split)
        else:
            anomalies_this_row.append((ANOMALY_UNKNOWN_SPLIT_TYPE, f"Unknown split type: '{raw_split}'. Expected equal/percentage/exact."))

        # Check for settlement-as-expense (common data entry error)
        if description.lower() in ("settlement", "payment", "payback", "paid back"):
            anomalies_this_row.append((ANOMALY_SETTLEMENT_AS_EXPENSE, f"Row looks like a settlement, not an expense: '{description}'"))

        # GROUP
        group_name = str(raw.get("group_name", "")).strip()
        group = db.query(Group).filter(Group.name == group_name).first()
        if not group:
            anomalies_this_row.append((ANOMALY_GROUP_NOT_FOUND, f"Group '{group_name}' not found in database"))

        # PAYER
        paid_by_name = str(raw.get("paid_by", "")).strip()
        payer = None
        if not paid_by_name or paid_by_name.lower() == "nan":
            anomalies_this_row.append((ANOMALY_MISSING_PAYER, "paid_by field is empty"))
        else:
            payer = db.query(User).filter(User.name == paid_by_name).first()
            if not payer:
                anomalies_this_row.append((ANOMALY_USER_NOT_FOUND, f"User '{paid_by_name}' not found"))
            elif group:
                # Check payer is actually in the group
                membership = db.query(GroupMember).filter(
                    GroupMember.group_id == group.id,
                    GroupMember.user_id == payer.id,
                ).first()
                if not membership:
                    anomalies_this_row.append((ANOMALY_PAYER_NOT_IN_GROUP, f"Payer '{paid_by_name}' is not a member of group '{group_name}'"))

        # PARTICIPANTS
        # CSV format: participants column = "Aisha,Rohan,Priya" for equal split
        # For percentage: "Aisha:50,Rohan:30,Priya:20"
        # For exact: "Aisha:400,Rohan:350,Priya:250"
        participants_raw = str(raw.get("participants", "")).strip()
        participants = []
        participant_users = []

        if not participants_raw or participants_raw.lower() == "nan":
            anomalies_this_row.append((ANOMALY_MISSING_PARTICIPANTS, "No participants listed"))
        elif group and split_type is not None and amount and amount > 0:
            entries = [e.strip() for e in participants_raw.split(",")]
            total_value = Decimal("0")

            for entry in entries:
                if ":" in entry:
                    parts = entry.split(":", 1)
                    uname = parts[0].strip()
                    try:
                        val = Decimal(parts[1].strip())
                    except InvalidOperation:
                        anomalies_this_row.append((ANOMALY_INVALID_AMOUNT, f"Invalid participant value for '{uname}': '{parts[1]}'"))
                        continue
                else:
                    uname = entry
                    val = None

                u = db.query(User).filter(User.name == uname).first()
                if not u:
                    anomalies_this_row.append((ANOMALY_USER_NOT_FOUND, f"Participant '{uname}' not found"))
                    continue

                # Check participant is in the group
                mem = db.query(GroupMember).filter(
                    GroupMember.group_id == group.id,
                    GroupMember.user_id == u.id,
                ).first()
                if not mem:
                    anomalies_this_row.append((ANOMALY_PARTICIPANT_NOT_IN_GROUP, f"Participant '{uname}' is not in group '{group_name}'"))
                    continue

                participant_users.append({"user_id": u.id, "value": val})
                if val:
                    total_value += val

            # Validate percentage/exact totals
            if split_type == SplitType.PERCENTAGE and participant_users:
                if abs(total_value - Decimal("100")) > Decimal("0.5"):
                    anomalies_this_row.append((ANOMALY_PERCENTAGE_NOT_100, f"Percentages sum to {total_value}, expected 100"))

            if split_type == SplitType.EXACT and participant_users and amount:
                if abs(total_value - amount) > Decimal("0.5"):
                    anomalies_this_row.append((ANOMALY_EXACT_SUM_MISMATCH, f"Exact amounts sum to {total_value}, expected {amount}"))

        # DUPLICATE CHECK: same description + amount + date + group + payer
        if group and payer and expense_date and amount:
            duplicate = db.query(Expense).filter(
                Expense.group_id == group.id,
                Expense.paid_by_id == payer.id,
                Expense.description == description,
                Expense.amount == amount,
            ).first()
            if duplicate:
                anomalies_this_row.append((ANOMALY_DUPLICATE_EXPENSE, f"Possible duplicate of Expense ID {duplicate.id}: same description, amount, group, and payer"))

        # ── 2. Log all anomalies for this row ─────────────────────────────────
        for anomaly_type, anomaly_desc in anomalies_this_row:
            action = "pending_review" if anomaly_type == ANOMALY_DUPLICATE_EXPENSE else "skipped"
            _log_anomaly(db, session.id, row_num, anomaly_type, anomaly_desc, raw, action)
            anomaly_count += 1

        # ── 3. Decide whether to import this row ──────────────────────────────
        # We skip a row if it has any BLOCKING anomaly.
        # Duplicate is non-blocking (pending review), future date is a warning.
        blocking_types = {
            ANOMALY_MISSING_PAYER, ANOMALY_PAYER_NOT_IN_GROUP,
            ANOMALY_INVALID_AMOUNT, ANOMALY_NEGATIVE_AMOUNT, ANOMALY_ZERO_AMOUNT,
            ANOMALY_INVALID_DATE, ANOMALY_GROUP_NOT_FOUND, ANOMALY_USER_NOT_FOUND,
            ANOMALY_PARTICIPANT_NOT_IN_GROUP, ANOMALY_UNKNOWN_SPLIT_TYPE,
            ANOMALY_MISSING_PARTICIPANTS, ANOMALY_PERCENTAGE_NOT_100,
            ANOMALY_EXACT_SUM_MISMATCH,
        }
        blocking_anomalies = [a for a, _ in anomalies_this_row if a in blocking_types]

        if blocking_anomalies:
            skipped += 1
            continue  # Don't import - move to next row

        # ── 4. Import the row ─────────────────────────────────────────────────
        if not (group and payer and expense_date and amount and split_type and participant_users):
            skipped += 1
            continue

        try:
            amount_inr = convert_to_inr(amount, currency)

            expense = Expense(
                group_id=group.id,
                paid_by_id=payer.id,
                description=description,
                amount=amount,
                currency=currency,
                amount_inr=amount_inr,
                split_type=split_type,
                expense_date=expense_date,
                import_session_id=session.id,
                notes=f"Imported from {filename}",
            )
            db.add(expense)
            db.flush()  # Get expense.id

            # Calculate and save splits
            splits = calculate_splits(amount_inr, split_type, participant_users)
            for uid, owed in splits.items():
                db.add(ExpenseSplit(
                    expense_id=expense.id,
                    user_id=uid,
                    owed_amount=owed,
                ))

            imported += 1

        except Exception as e:
            _log_anomaly(db, session.id, row_num, "import_error", str(e), raw, "skipped")
            anomaly_count += 1
            skipped += 1

    # ── 5. Finalize session ───────────────────────────────────────────────────
    session.imported_rows = imported
    session.skipped_rows = skipped
    session.anomaly_count = anomaly_count
    session.status = "completed"
    db.commit()

    return session


def _log_anomaly(
    db: Session,
    session_id: int,
    row_number: int,
    anomaly_type: str,
    description: str,
    raw_data: dict,
    action_taken: str,
) -> None:
    """Helper to create an ImportAnomaly record."""
    # Convert raw_data values to strings for JSON serialization
    safe_raw = {k: str(v) for k, v in raw_data.items()}
    anomaly = ImportAnomaly(
        import_session_id=session_id,
        row_number=row_number,
        anomaly_type=anomaly_type,
        description=description,
        raw_data=safe_raw,
        action_taken=action_taken,
        reviewed="pending",
    )
    db.add(anomaly)
    db.flush()
