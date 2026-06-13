# DECISIONS.md — Architecture and Design Decisions

---

## Decision 1: Relational Database (PostgreSQL) over NoSQL

**Problem:** Choose a database for storing users, groups, expenses, splits, and settlements.

**Options considered:**
- PostgreSQL (relational)
- MongoDB (document/NoSQL)
- SQLite (file-based relational)

**Chosen:** PostgreSQL

**Why:** Expenses are inherently relational. An `ExpenseSplit` references an `Expense`, which references a `Group`, which references `Users`. SQL JOINs are the natural way to express this. Referential integrity means you physically cannot create a split for a non-existent expense — the database enforces correctness. MongoDB would require enforcing these relationships in application code, which is error-prone. SQLite was rejected because it doesn't support concurrent connections well and isn't production-grade for a deployed app.

---

## Decision 2: Store `amount_inr` on every Expense

**Problem:** Expenses can be in INR or USD. Balance calculations must be in a single currency.

**Options considered:**
- Convert at query time (always calculate INR from amount + currency when needed)
- Store the INR-equivalent at write time (`amount_inr` column)

**Chosen:** Store `amount_inr` at write time

**Why:** Converting at query time means every balance calculation must re-run the conversion logic. This adds complexity to SQL queries and means a change in the exchange rate would retroactively change historical balances (which is wrong). Storing `amount_inr` at write time means: "this expense was worth ₹X at the time it was entered." Historical balances stay stable. The trade-off is the `amount_inr` column could become stale if the rate changes, but for this project we use a fixed rate documented in `currency.py`.

---

## Decision 3: Fixed Exchange Rate (USD → INR = 83.50)

**Problem:** USD expenses need to be converted to INR for balance calculations.

**Options considered:**
- Live exchange rate API (e.g., Open Exchange Rates, Fixer.io)
- Fixed rate

**Chosen:** Fixed rate (₹83.50 per USD)

**Why:** A live API requires an API key, adds a network call on every expense creation, can fail, and adds latency. For an internship assignment, a fixed rate is a reasonable simplification. This is documented in `currency.py` and `DECISIONS.md` so any reviewer can find it instantly. In production, I would use a live API and cache the rate for 1 hour.

---

## Decision 4: Pre-calculate Splits and Store Them

**Problem:** How to store how much each participant owes for each expense.

**Options considered:**
- Store split type + participants, recalculate at read time
- Pre-calculate and store each person's share in `expense_splits` table

**Chosen:** Pre-calculate and store in `expense_splits`

**Why:** Recalculating at read time means balance queries must re-run split math on every API call. Pre-storing means balance calculation is a simple `SUM(owed_amount)` SQL query. It also means the split is immutable — if someone's percentage changes or the calculation logic changes, historical splits are unaffected. The trade-off is slightly more storage, which is negligible for this scale.

---

## Decision 5: `joined_at` / `left_at` on GroupMember instead of deleting rows

**Problem:** How to handle a user leaving a group (Sam's requirement).

**Options considered:**
- Delete the `GroupMember` row when someone leaves
- Add `left_at` timestamp column, set it when they leave

**Chosen:** Soft delete with `left_at`

**Why:** If we delete the row, we lose history. We can no longer answer "was Sam a member when this expense was created?" The balance engine checks `joined_at <= expense_date` and `(left_at IS NULL OR left_at >= expense_date)`. This is the only correct way to satisfy Sam's requirement.

---

## Decision 6: Greedy Debt Simplification Algorithm

**Problem:** How to present "who pays whom" (Aisha's requirement) in the simplest form.

**Options considered:**
- Show every raw balance pair (N×N matrix)
- Greedy simplification: match largest debtor with largest creditor

**Chosen:** Greedy simplification

**Why:** Without simplification, 5 people in a group could have 10+ individual debt pairs. The greedy algorithm reduces this to the minimum number of transactions (at most N-1 for N people). The algorithm is simple to explain: sort creditors and debtors by amount, match them largest-to-largest, repeat. It produces a correct (not necessarily globally optimal) solution in O(N log N) time, which is more than sufficient.

---

## Decision 7: Duplicate anomalies go to "pending review" instead of being auto-skipped

**Problem:** What to do when the importer finds a possible duplicate expense.

**Options considered:**
- Auto-skip duplicates silently
- Auto-skip duplicates with a log
- Flag for human review

**Chosen:** Flag for human review (pending_review)

**Why:** Meera's requirement: "Duplicates must be reviewed before deletion." Two expenses for the same amount at the same restaurant are suspicious but not definitely wrong. Only the user knows if it was a real duplicate or two separate events. Auto-skipping could silently lose real data. Auto-importing could create real duplicates. Human review is the correct answer.

---

## Decision 8: JWT tokens stored in localStorage

**Problem:** Where to store the authentication token in the browser.

**Options considered:**
- `localStorage`
- `httpOnly` cookies

**Chosen:** `localStorage`

**Why:** `httpOnly` cookies are more secure (not accessible to JavaScript, protecting against XSS), but require same-site cookie configuration and CORS setup that adds complexity. For this project, `localStorage` is the standard choice for React SPAs calling a separate API domain. In production with sensitive financial data, I would move to `httpOnly` cookies.

---

## Decision 9: Separate `ImportSessions` and `ImportAnomalies` tables

**Problem:** How to persist import history and anomaly details.

**Options considered:**
- Log to a file
- Store in a single JSON column on the session
- Two separate tables

**Chosen:** Two separate tables

**Why:** Two tables allow querying. You can ask: "Show me all pending anomalies across all imports" (used in the Anomaly Review page). A JSON column can't be efficiently queried. A log file can't be queried at all. Rohan's requirement for "complete transparency and traceability" requires persistent, queryable anomaly records.

---

## Decision 10: Name-based user matching in CSV import

**Problem:** The CSV identifies users by name (e.g., "Aisha"), not by ID.

**Options considered:**
- Match by name (case-sensitive)
- Match by email
- Fuzzy matching

**Chosen:** Exact name match (case-sensitive)

**Why:** The CSV format uses names. Email would require adding an email column to the CSV. Fuzzy matching is complex and could incorrectly match "Dev" to "Devika". Exact match is predictable and auditable — if a name doesn't match, it's an anomaly that the user must fix. This avoids silent incorrect matches.
