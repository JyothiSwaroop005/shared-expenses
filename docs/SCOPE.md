# SCOPE.md — Anomaly Detection Strategy

This document defines every anomaly the CSV importer can detect, how it detects it, how it handles it, and why.

---

## Anomaly 1: Missing Required Column

**Detection:** After reading the CSV, check `set(df.columns)` against `REQUIRED_COLUMNS`. If any required column is absent, the entire file is unprocessable.

**Handling:** Log one anomaly at row 0 (file-level), set session status to "failed", return immediately.

**Reason:** Without required columns (e.g., `amount`, `paid_by`), no row can be safely imported. Processing further would produce meaningless data.

**Risk:** HIGH — entire import fails.

---

## Anomaly 2: Missing Payer

**Detection:** `paid_by` field is empty, whitespace-only, or the string "nan" (pandas default for empty cells).

**Handling:** Log as `missing_payer`, mark row as **skipped** (blocking).

**Reason:** An expense without a payer cannot be correctly attributed. We cannot assume who paid.

**Risk:** HIGH — skipping is correct.

---

## Anomaly 3: Payer Not In Group

**Detection:** `paid_by` resolves to a known user, but that user has no `GroupMember` record for the target group.

**Handling:** Log as `payer_not_in_group`, mark row as **skipped** (blocking).

**Reason:** A person cannot pay for a group expense if they are not a member. Importing this would corrupt group balances.

**Risk:** HIGH — could create phantom balances.

---

## Anomaly 4: Invalid Amount

**Detection:** `amount` field cannot be parsed as a Decimal (e.g., "abc", "N/A", "₹1,200").

**Handling:** Log as `invalid_amount`, mark row as **skipped** (blocking).

**Reason:** Without a valid amount, the expense is undefined. We cannot default to zero or guess.

**Risk:** HIGH.

---

## Anomaly 5: Negative Amount

**Detection:** `amount` parses successfully but the value is less than zero.

**Handling:** Log as `negative_amount`, mark row as **skipped** (blocking).

**Reason:** Expenses cannot be negative. A refund or credit should be handled as a separate settlement, not a negative expense.

**Risk:** HIGH — negative amounts would invert balances.

---

## Anomaly 6: Zero Amount

**Detection:** `amount` is exactly 0.00.

**Handling:** Log as `zero_amount`, mark row as **skipped** (blocking).

**Reason:** A zero-amount expense has no financial meaning and would add noise to the database.

**Risk:** MEDIUM.

---

## Anomaly 7: Future Date

**Detection:** `expense_date` parses successfully but is after `datetime.now(UTC)`.

**Handling:** Log as `future_date` with action **imported_with_warning** (non-blocking). The expense is imported.

**Reason:** Future dates could be intentional (e.g., pre-logging a booking). We warn but do not block, because blocking would lose legitimate data. The user can review in Anomaly Review.

**Risk:** LOW — imported with a flag.

---

## Anomaly 8: Invalid Date

**Detection:** `expense_date` cannot be parsed by `pd.to_datetime()` (e.g., "not-a-date", "32/13/2024").

**Handling:** Log as `invalid_date`, mark row as **skipped** (blocking).

**Reason:** Without a date, we cannot check membership windows (Sam's requirement) or sort expenses chronologically.

**Risk:** HIGH.

---

## Anomaly 9: Invalid Currency

**Detection:** `currency` field is not in `{"INR", "USD"}`.

**Handling:** Log as `invalid_currency`, default to INR, continue processing (non-blocking warning).

**Reason:** The assignment specifies INR and USD only. Defaulting to INR is the safest assumption for an India-based app. The anomaly is logged so the user knows a substitution was made.

**Risk:** MEDIUM — data is imported with a substitution, which is clearly logged.

---

## Anomaly 10: Unknown Split Type

**Detection:** `split_type` is not one of `{"equal", "percentage", "exact"}`.

**Handling:** Log as `unknown_split_type`, mark row as **skipped** (blocking).

**Reason:** Without a valid split type, we cannot calculate how to divide the expense. We cannot default because each split type has fundamentally different logic.

**Risk:** HIGH.

---

## Anomaly 11: Group Not Found

**Detection:** `group_name` does not match any `Group.name` in the database (case-sensitive).

**Handling:** Log as `group_not_found`, mark row as **skipped** (blocking).

**Reason:** We cannot create groups on-the-fly during import — that would bypass the normal group creation flow (membership tracking, created_by, etc.).

**Risk:** HIGH.

---

## Anomaly 12: User Not Found

**Detection:** A name in `paid_by` or `participants` does not match any `User.name` in the database.

**Handling:** Log as `user_not_found`, mark row as **skipped** (blocking).

**Reason:** We match users by name (as provided in the CSV). If no user matches, we cannot determine who is involved.

**Risk:** HIGH.

---

## Anomaly 13: Participant Not In Group

**Detection:** A participant resolves to a known user, but they have no membership in the target group.

**Handling:** Log as `participant_not_in_group`, mark row as **skipped** (blocking).

**Reason:** Splitting an expense to someone outside the group would create a balance that cannot be settled within the group context.

**Risk:** HIGH.

---

## Anomaly 14: Percentage Sum Not 100

**Detection:** For percentage splits, sum all participant values. If `abs(sum - 100) > 0.5`, it's an anomaly.

**Handling:** Log as `percentage_sum_not_100`, mark row as **skipped** (blocking).

**Reason:** Percentages must sum to exactly 100% (with 0.5% tolerance for rounding). Otherwise the expense amount is not fully allocated.

**Risk:** HIGH — unallocated amounts corrupt balances.

---

## Anomaly 15: Exact Sum Mismatch

**Detection:** For exact splits, sum all participant values. If `abs(sum - amount) > 0.5`, it's an anomaly.

**Handling:** Log as `exact_sum_mismatch`, mark row as **skipped** (blocking).

**Reason:** The individual exact amounts must equal the total expense amount. A mismatch means money is unaccounted for or over-allocated.

**Risk:** HIGH.

---

## Anomaly 16: Duplicate Expense

**Detection:** Query the database for an existing expense with the same `group_id`, `paid_by_id`, `description`, and `amount`. If found, flag as duplicate.

**Handling:** Log as `duplicate_expense`, mark as **pending_review** (non-blocking). The row is NOT imported until a human reviews it.

**Reason:** Meera's requirement: "Duplicates must be reviewed before deletion." A duplicate could be legitimate (two people paying the same restaurant on different occasions) or a data entry error. Only a human can decide.

**Risk:** MEDIUM — held for review rather than silently dropped or silently imported.

---

## Anomaly 17: Settlement Logged as Expense

**Detection:** `description` matches keywords: "settlement", "payment", "payback", "paid back" (case-insensitive).

**Handling:** Log as `settlement_as_expense`, mark as **pending_review** (non-blocking warning).

**Reason:** A common data entry mistake is recording "Rohan paid back Aisha" as an expense instead of a settlement. Settlements and expenses have opposite effects on balances. This is flagged for human review.

**Risk:** HIGH if imported silently — would double-count debt.

---

## Anomaly 18: Missing Participants

**Detection:** `participants` field is empty, whitespace-only, or "nan".

**Handling:** Log as `missing_participants`, mark row as **skipped** (blocking).

**Reason:** Without participants, we cannot create any `ExpenseSplit` rows, making the expense meaningless for balance calculation.

**Risk:** HIGH.

---

## Summary Table

| # | Anomaly Type | Blocking? | Default Action |
|---|---|---|---|
| 1 | missing_required_column | Yes (file-level) | Fail entire import |
| 2 | missing_payer | Yes | Skip row |
| 3 | payer_not_in_group | Yes | Skip row |
| 4 | invalid_amount | Yes | Skip row |
| 5 | negative_amount | Yes | Skip row |
| 6 | zero_amount | Yes | Skip row |
| 7 | future_date | No | Import with warning |
| 8 | invalid_date | Yes | Skip row |
| 9 | invalid_currency | No | Default to INR, warn |
| 10 | unknown_split_type | Yes | Skip row |
| 11 | group_not_found | Yes | Skip row |
| 12 | user_not_found | Yes | Skip row |
| 13 | participant_not_in_group | Yes | Skip row |
| 14 | percentage_sum_not_100 | Yes | Skip row |
| 15 | exact_sum_mismatch | Yes | Skip row |
| 16 | duplicate_expense | No | Pending human review |
| 17 | settlement_as_expense | No | Pending human review |
| 18 | missing_participants | Yes | Skip row |
## CSV Schema Mismatch

Issue:
The provided CSV contained the column `date` while the importer expected `expense_date`.

Issue:
The provided CSV did not contain a `group_name` column.

Action Taken:
The import process detected the schema mismatch, prevented invalid data from being imported, and generated an anomaly report for manual review.

Evidence:
- Missing required column: expense_date
- Missing required column: group_name
- 42 rows analyzed
- Import rejected and anomaly recorded