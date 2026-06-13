# AI_USAGE.md — How AI Was Used in This Project

## Tools Used

- **Claude (Anthropic)** — Primary tool for code generation, architecture planning, and documentation drafting
- **GitHub Copilot** — Inline suggestions during manual editing sessions

---

## How AI Was Used

### 1. Architecture Planning
Prompted Claude to suggest a folder structure for a FastAPI + React app with these specific requirements (group membership over time, CSV import with anomaly detection, multiple split types).

### 2. Schema Design
Prompted Claude to design a PostgreSQL schema. Reviewed the output, then manually adjusted the `GroupMember` model to add `joined_at` and `left_at` (the AI initially only included a boolean `is_active` which would not satisfy Sam's requirement).

### 3. Balance Engine
Prompted Claude to write the greedy debt simplification algorithm. The logic was correct but the initial version did not handle Decimal precision correctly (see AI Mistake #1 below).

### 4. CSV Importer
Prompted Claude to write the anomaly detection logic. Required multiple iterations to cover all 18 anomaly types.

### 5. Documentation
SCOPE.md and DECISIONS.md were initially drafted with AI assistance, then heavily edited to add project-specific reasoning.

---

## AI Mistakes Detected and Fixed

### Mistake 1: Float arithmetic in balance calculations

**What AI generated:**
```python
# AI used regular Python floats
base_share = amount_inr / len(participants)
```

**Problem detected:** When splitting ₹100 among 3 people, Python float division gives:
```
33.333333333333336
```
Multiplied by 3: `100.00000000000001` — not exactly ₹100. Over many expenses this compounds into balance errors like "Rohan owes ₹0.001" which is meaningless.

**How it was detected:** Wrote a manual test: split ₹100 among 3 people, summed the shares, checked if they equaled ₹100 exactly. They didn't.

**How it was fixed:** Replaced all `float` arithmetic with Python's `Decimal` type and used `ROUND_HALF_UP` rounding. Added the "remainder goes to the first person" logic to ensure splits always sum exactly to the total.

```python
# Fixed version
from decimal import Decimal, ROUND_HALF_UP
base_share = (amount_inr / n).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
remainder = amount_inr - (base_share * n)
# First person absorbs the rounding remainder
```

---

### Mistake 2: AI used `unique=True` on GroupMember (group_id, user_id)

**What AI generated:**
```python
# AI added a UniqueConstraint thinking a user can only be in a group once
__table_args__ = (UniqueConstraint("group_id", "user_id"),)
```

**Problem detected:** Sam's scenario requires a user to potentially leave and rejoin a group. A unique constraint on `(group_id, user_id)` would prevent a second row being created when the user rejoins, even though the first row has `left_at` set.

**How it was detected:** Traced through the "user leaves group, then rejoins later" scenario manually. Adding the second `GroupMember` row would fail with a unique constraint violation.

**How it was fixed:** Removed the `UniqueConstraint`. The application layer enforces that a user cannot have two *active* memberships (where `left_at IS NULL`) by checking before inserting in the `add_member` router endpoint.

---

### Mistake 3: AI generated synchronous file reading for the CSV upload endpoint

**What AI generated:**
```python
@router.post("/imports/")
def upload_csv(file: UploadFile = File(...)):
    contents = file.file.read()  # Synchronous read inside async context
```

**Problem detected:** FastAPI's `UploadFile.file.read()` is a synchronous call. Inside an `async def` endpoint, this blocks the entire event loop while reading the file, degrading performance for concurrent requests.

**How it was detected:** The FastAPI documentation explicitly warns about this. Noticed the inconsistency when reviewing the generated code.

**How it was fixed:** Changed the endpoint to `async def` and used `await file.read()`:

```python
@router.post("/imports/")
async def upload_csv(file: UploadFile = File(...)):
    contents = await file.read()  # Non-blocking async read
```

---

## Key Takeaway

AI was a useful accelerator for boilerplate code (models, schemas, routers) but required careful human review for:
- Numeric precision (always use `Decimal` for money)
- Business logic edge cases (rejoin scenarios, membership windows)
- Async/sync correctness in FastAPI
- Security considerations (password hashing, JWT storage)

Every AI-generated file was read line by line before being included in the project.
