# Interview Preparation — 50 Technical Questions

---

## DATABASE DESIGN

**Q1: Why did you use PostgreSQL instead of MongoDB?**

Answer: Expenses are relational by nature. An ExpenseSplit references an Expense, which references a Group, which references Users. SQL JOINs handle this naturally and referential integrity prevents orphan records at the database level. MongoDB would require enforcing these relationships in application code, which is more error-prone. PostgreSQL also gives us ACID transactions, meaning if creating an expense and its splits partially fails, everything rolls back — critical for financial data.

Follow-up: "What is referential integrity?" → The database enforces that foreign key values must exist in the referenced table. You cannot create an `expense_split` row pointing to `expense_id = 999` if that expense doesn't exist.

---

**Q2: Why is there a separate `expense_splits` table instead of storing splits as a JSON column?**

Answer: If splits were a JSON column, I could not query "what does Rohan owe across all expenses?" with a simple SQL SUM. Normalized rows allow `SELECT SUM(owed_amount) FROM expense_splits WHERE user_id = ?` which is efficient and indexed. JSON columns are opaque to SQL aggregations.

Follow-up: "When would you use a JSON column?" → For truly variable, non-queryable metadata (e.g., storing a raw CSV row for audit purposes — which is exactly what I do in `import_anomalies.raw_data`).

---

**Q3: Why does GroupMember have `joined_at` and `left_at` instead of just deleting the row?**

Answer: Sam's requirement: "I joined later. Earlier expenses should not affect me." If we deleted the row, we'd lose history. With `joined_at` and `left_at`, I can query: "was this user a member when this expense was created?" by checking `joined_at <= expense_date AND (left_at IS NULL OR left_at >= expense_date)`. Deleting rows destroys auditability.

Follow-up: "What is this pattern called?" → Soft delete / temporal data pattern.

---

**Q4: Why do you store `amount_inr` as a separate column on expenses?**

Answer: All balance calculations work in INR. Computing `amount_inr` at query time would mean every balance query must re-run currency conversion logic, and historical balances would change if the exchange rate changed. Storing it at write time creates an immutable record of "this expense was worth ₹X when it was logged."

Follow-up: "What if the exchange rate was wrong when it was stored?" → It stays as-is. We log the rate used in `currency.py`. The user can delete and re-enter the expense if needed.

---

**Q5: Why do you use `Numeric(10, 2)` instead of `Float` for money?**

Answer: Floating-point numbers cannot represent all decimal fractions exactly. `0.1 + 0.2` in Python floats is `0.30000000000000004`. For money, these errors compound. `Numeric(10, 2)` is an exact decimal type — it stores and returns exactly what you put in, with no floating-point drift.

Follow-up: "What Python type do you use in code?" → `Decimal` from Python's `decimal` module.

---

## BALANCE ENGINE

**Q6: Walk me through how you calculate who owes whom.**

Answer: Three steps. First, for every expense, the payer gets +amount_inr to their balance (they're owed that money back). Second, every expense_split row subtracts owed_amount from the participant's balance (they owe that much). Third, settlements adjust balances: the payer gets +amount_inr (they paid off debt) and the payee gets -amount_inr (they've been paid back). Positive final balance = owed money. Negative = owes money.

---

**Q7: What is the debt simplification algorithm and why did you use it?**

Answer: Greedy simplification. Separate everyone into creditors (positive balance) and debtors (negative balance), sorted by amount. Match the largest debtor with the largest creditor. The debtor pays the minimum of what they owe and what the creditor is owed. Repeat. This produces at most N-1 transactions for N people, vs potentially O(N²) without simplification. It's Aisha's "one number per person" requirement.

Follow-up: "Is this always the minimum number of transactions?" → The greedy approach produces a correct and near-optimal solution but not always the mathematical minimum. Computing the true minimum is NP-hard. For groups under 50 people, greedy is indistinguishable from optimal.

---

**Q8: How does Sam's join date affect balance calculations?**

Answer: In `get_group_balances`, for every expense split, I query GroupMember to check if the user was active at the time of the expense: `joined_at <= expense_date AND (left_at IS NULL OR left_at >= expense_date)`. If no such membership exists, the split is skipped — the user doesn't owe for expenses before they joined.

Follow-up: "What if someone has two memberships (left and rejoined)?" → There would be two rows. The query checks if ANY row satisfies the date condition, so it handles rejoin correctly.

---

**Q9: How do you handle the equal split rounding problem?**

Answer: Splitting ₹100 among 3 people: 100/3 = 33.333... I quantize to 33.33. Three times 33.33 = 99.99, leaving ₹0.01 unallocated. I assign the remainder to the first person: they get 33.34, others get 33.33. The total always equals exactly the original amount.

Follow-up: "Why the first person?" → Arbitrary but deterministic. In Splitwise-style apps the payer often absorbs the remainder. Any consistent rule works — the key is that splits always sum to the total.

---

**Q10: How does currency conversion work?**

Answer: I use a fixed rate of ₹83.50 per USD, documented in `currency.py`. When an expense is created in USD, I call `convert_to_inr(amount, currency)` which multiplies by 83.50 and rounds to 2 decimal places. The result is stored in `amount_inr`. All balance calculations use `amount_inr` only.

---

## CSV IMPORTER

**Q11: How does your CSV importer avoid crashing on bad data?**

Answer: Every piece of parsing is inside a try-except block. If pandas can't parse an amount, it logs an anomaly and continues to the next row. The importer never raises an exception from bad data — it catches all errors, logs them as anomalies, and moves on. The only case where the whole import fails is if the file itself can't be read as a CSV.

---

**Q12: What's the difference between a blocking and non-blocking anomaly?**

Answer: A blocking anomaly means the row cannot be imported — we don't have enough valid data to create a meaningful expense (e.g., missing payer, invalid amount). A non-blocking anomaly means the row is imported but with a warning (e.g., future date, unknown currency defaulted to INR). The distinction prevents us from losing potentially valid data while still flagging problems.

---

**Q13: How do you detect duplicate expenses?**

Answer: Before importing each row, I query the database for an existing expense with the same `group_id`, `paid_by_id`, `description`, and `amount`. If found, I flag it as `duplicate_expense` with `action_taken = "pending_review"`. The row is NOT imported until a human approves or rejects it in the Anomaly Review page. This satisfies Meera's requirement.

Follow-up: "Why not use a unique database constraint?" → Because two identical-looking expenses might be legitimate (same restaurant, same price, different day). Only a human can decide.

---

**Q14: How do you detect a settlement logged as an expense?**

Answer: I check if the `description` field contains keywords like "settlement", "payment", "payback", or "paid back" (case-insensitive). If yes, it's flagged as `settlement_as_expense` for review. This is a heuristic — it could have false positives, which is why it goes to human review rather than being auto-skipped.

---

**Q15: Why do you store the raw CSV row in `import_anomalies.raw_data`?**

Answer: Rohan's requirement: "complete transparency and traceability." When someone reviews a flagged row, they need to see exactly what was in the CSV — not a processed version, but the raw original. This lets them make an informed decision. We store it as JSON with all values as strings (since pandas may infer types).

---

## FASTAPI / BACKEND

**Q16: What is a FastAPI dependency and how do you use it?**

Answer: A dependency is a function that FastAPI calls and injects into route handlers. `get_db()` creates and closes a database session. `get_current_user()` reads the JWT token and returns the logged-in User. Any endpoint that uses `Depends(get_current_user)` is automatically protected — FastAPI returns 401 if the token is invalid without any code in the endpoint itself.

---

**Q17: Why do you use `db.flush()` before `db.commit()` in some places?**

Answer: `flush()` sends the SQL to the database but doesn't commit the transaction. This means I can get the auto-generated ID (e.g., `expense.id`) to use in subsequent rows (e.g., `ExpenseSplit.expense_id = expense.id`) within the same transaction. If anything fails after `flush()` but before `commit()`, the whole transaction rolls back — the flush is not permanent.

---

**Q18: How does JWT authentication work in your app?**

Answer: On login, the server creates a JWT token containing the user's ID, signed with a secret key. The client stores this token in localStorage and sends it in the `Authorization: Bearer <token>` header on every request. The server's `get_current_user` dependency decodes the token, verifies the signature, extracts the user ID, and queries the database for the user. If the token is expired or tampered with, `decode_access_token` returns None and FastAPI returns 401.

---

**Q19: Why do you use `pool_pre_ping=True` in SQLAlchemy?**

Answer: Neon PostgreSQL is serverless — connections can go idle and be dropped. `pool_pre_ping=True` tells SQLAlchemy to test each connection with a lightweight query before using it. If the connection is dead, it reconnects automatically. Without this, you'd get connection errors on the first request after an idle period.

---

**Q20: What is the difference between SQLAlchemy models and Pydantic schemas?**

Answer: SQLAlchemy models define the database table structure — columns, types, relationships. Pydantic schemas define what the API accepts and returns — validation rules, field types, what's optional. They're separate because the API shape often differs from the database shape. For example, the User model has `hashed_password`, but the UserOut schema omits it entirely so it's never exposed via the API.

---

## FRONTEND

**Q21: Why do you use React Context for auth state?**

Answer: The logged-in user needs to be accessible throughout the app — in the Navbar, in pages, in components. Without Context, you'd have to pass the user as a prop through every component layer ("prop drilling"). Context makes the user available to any component that calls `useAuth()` without any intermediate components needing to know about it.

---

**Q22: Why are all API calls in one file (client.js)?**

Answer: Single source of truth. If the backend URL changes (e.g., Render gives you a new domain), I change `BASE_URL` in one place and every API call is updated. The axios interceptors (attach JWT token, handle 401s) are also defined once and apply to all requests automatically.

---

**Q23: What does your axios interceptor do?**

Answer: Two things. The request interceptor reads the JWT token from localStorage and adds it to every request's `Authorization` header — so I never need to manually add the header in each API call. The response interceptor catches 401 errors: if any API call returns 401, it clears the token from localStorage and redirects to `/login`. This handles expired tokens gracefully.

---

**Q24: What is `useSearchParams` used for in your Expenses page?**

Answer: It reads query parameters from the URL (e.g., `/expenses?group=3`). When the user clicks "Add Expense" from a GroupDetail page, I link to `/expenses?group=3` and the Expenses page pre-selects that group. This makes the UX flow naturally without needing to pass state through routing.

---

**Q25: Why does ProtectedRoute check `loading` before redirecting?**

Answer: On page load, the component reads localStorage to restore the user session. This is synchronous but React renders before the `useEffect` runs. If `loading` is true and the user IS logged in (just not yet restored from localStorage), we'd flash a redirect to `/login` for a split second. Returning `null` while loading prevents this flicker.

---

## SECURITY

**Q26: How do you store passwords?**

Answer: Using bcrypt hashing via passlib. The plain text password is never stored — `hash_password()` converts it to a bcrypt hash that includes the salt. `verify_password()` uses bcrypt's verify function to check if a plain text password matches the hash. Bcrypt is intentionally slow (configurable work factor) to make brute-force attacks impractical.

---

**Q27: What are CORS headers and why do you need them?**

Answer: CORS (Cross-Origin Resource Sharing) is a browser security feature that blocks JavaScript from making requests to a different domain than the page it's on. My frontend is on `localhost:5173` and the backend is on `localhost:8000` — different ports, so different origins. Without CORS headers, the browser would block all API calls. FastAPI's `CORSMiddleware` adds the necessary response headers to tell browsers "this origin is allowed."

---

**Q28: Why is your JWT secret key important?**

Answer: The secret key is used to sign JWTs. If someone knows your secret key, they can forge valid tokens for any user ID and bypass authentication entirely. The key must be: long (32+ characters), random, and never committed to git. That's why it's in `.env` and `.env` is in `.gitignore`.

---

## DEPLOYMENT

**Q29: What happens when you deploy to Render?**

Answer: Render reads the Dockerfile, builds a Docker image with Python and the dependencies, and runs `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. The `$PORT` environment variable is set by Render. `0.0.0.0` means "listen on all network interfaces" — necessary for containerized deployments where `localhost` would only listen internally.

---

**Q30: What is Neon PostgreSQL and why use it?**

Answer: Neon is a serverless PostgreSQL provider. "Serverless" means there's no always-on VM — the database scales to zero when idle and wakes up on the first query (causing a cold start). It has a generous free tier, supports standard PostgreSQL so there's no vendor lock-in, and provides a web console for running queries directly.

---

## BUSINESS LOGIC

**Q31: What happens if someone leaves a group but still has unsettled balances?**

Answer: Their `left_at` is set but their balance remains in the system. They still appear in group balance calculations for expenses during their membership period. The system doesn't force settlement on leaving — that's a UX decision. In a real app you'd probably warn the user and prompt settlement before they leave.

---

**Q32: How does a percentage split work end-to-end?**

Answer: The user provides participants with percentages like `[{user_id: 1, value: 50}, {user_id: 2, value: 30}, {user_id: 3, value: 20}]`. The importer validates they sum to 100. In `calculate_splits`, for each participant: `owed = (amount_inr * percentage / 100).quantize(0.01)`. The results are stored in `expense_splits`. For a ₹1000 expense: Aisha=₹500, Rohan=₹300, Priya=₹200.

---

**Q33: How does an exact split work?**

Answer: The user provides explicit amounts for each participant. The importer validates they sum to the total expense amount (within ₹0.50 tolerance for rounding). The exact values are stored directly in `expense_splits.owed_amount`. No calculation needed — the user has already specified the amounts.

---

**Q34: Can a user appear in both `payer` and `participants` for the same expense?**

Answer: Yes — this is the normal case. If Aisha pays ₹300 for dinner for Aisha, Rohan, and Priya, equal split: each owes ₹100. Aisha paid ₹300 (+300 to her balance) and owes ₹100 of her own share (-100 from her balance). Net: Aisha is owed ₹200. Rohan and Priya each owe ₹100. This is mathematically correct.

---

**Q35: How do settlements affect balances?**

Answer: Settlements are separate from expenses. In `get_group_balances`, after processing all expenses and splits, I iterate over settlements. For each settlement: the payer's balance increases by `amount_inr` (they've reduced their debt) and the payee's balance decreases (they've been paid back). This reduces the net amounts outstanding.

---

## ERROR HANDLING

**Q36: What HTTP status codes do you use and why?**

Answer:
- `200 OK` — successful GET
- `201 Created` — successful POST (resource created)
- `204 No Content` — successful DELETE (nothing to return)
- `400 Bad Request` — invalid input (e.g., percentages don't sum to 100)
- `401 Unauthorized` — missing or invalid JWT token
- `403 Forbidden` — authenticated but not allowed (e.g., deleting someone else's expense)
- `404 Not Found` — resource doesn't exist

---

**Q37: What happens if the CSV upload fails partway through?**

Answer: I use `db.flush()` for intermediate saves within the import loop but only call `db.commit()` at the end. If an unexpected exception occurs partway through, the `except` block in the CSV importer logs an anomaly for that row and continues. The session is committed at the end with whatever successfully imported. I don't wrap the whole import in a single transaction because for 1000-row files, atomic commit-or-fail-all would be too aggressive — partial success is better than total failure.

---

**Q38: What error does a user see if they try to add someone already in a group?**

Answer: The `add_member` endpoint queries for an existing active membership (where `left_at IS NULL`). If found, it raises `HTTPException(status_code=400, detail="User is already a member of this group")`. The frontend displays this `detail` string as an error message.

---

## TESTING (If asked)

**Q39: How would you test the balance engine?**

Answer: Unit tests with known inputs and expected outputs. Example: Create 3 users, one ₹300 equal-split expense paid by User 1. Expected: User1 balance = +200, User2 = -100, User3 = -100. Verify `simplify_debts` returns "User2 pays User1 ₹100, User3 pays User1 ₹100". Use pytest with a test SQLite database (or test PostgreSQL schema) that's reset between tests.

---

**Q40: How would you test the CSV importer?**

Answer: Create test CSV files with specific anomalies. For each anomaly type: assert that the correct `anomaly_type` is logged, the correct `action_taken` is set, and the correct number of rows are imported/skipped. Parametrize the tests: one test function, one test case per anomaly type. Also test the happy path: a clean CSV with no anomalies imports all rows successfully.

---

## GENERAL SOFTWARE ENGINEERING

**Q41: What is the difference between `db.flush()` and `db.commit()`?**

Answer: `flush()` sends pending SQL to the database within the current transaction — the changes are visible to subsequent queries in the same session, but not committed (other sessions can't see them yet). `commit()` permanently saves all changes and makes them visible to all database connections. After commit, changes survive a server restart. After flush (without commit), a subsequent `rollback()` would undo the flush.

---

**Q42: What is `cascade="all, delete-orphan"` on the Expense→splits relationship?**

Answer: When an Expense is deleted, SQLAlchemy automatically deletes all related ExpenseSplit rows. "delete-orphan" means if a split is removed from `expense.splits` collection (without deleting the expense), the orphaned split is also deleted. This prevents dangling split rows that reference a non-existent expense.

---

**Q43: Why do you use `server_default=func.now()` instead of `default=datetime.utcnow`?**

Answer: `server_default=func.now()` means the database computes the timestamp. `default=datetime.utcnow` means Python computes it. The database timestamp is more reliable because it's not affected by application server timezone settings, clock drift between multiple app servers, or the time between Python execution and the INSERT reaching the database.

---

**Q44: What is `from_attributes = True` in Pydantic Config?**

Answer: By default, Pydantic reads data from dictionaries. SQLAlchemy models are objects with attribute access (e.g., `expense.amount`), not dicts. `from_attributes = True` tells Pydantic: "read attributes from objects, not just dict keys." This allows `ExpenseOut.model_validate(expense_orm_object)` to work.

---

**Q45: What does `pool_size=5, max_overflow=10` mean in SQLAlchemy?**

Answer: The connection pool maintains up to 5 persistent connections to the database. If all 5 are busy, it can create up to 10 additional "overflow" connections. Beyond 15 simultaneous connections, new requests wait. For Neon's free tier with limited connections, keeping the pool small prevents hitting connection limits.

---

## REQUIREMENTS-SPECIFIC

**Q46: How does your app satisfy Aisha's requirement ("one number per person")?**

Answer: The `/balances/group/{id}` endpoint returns `simplified_transactions`: a list of `{from_user, to_user, amount}` entries representing the minimum set of payments to settle all debts. The Balances page displays this as "Rohan pays Aisha ₹300" — exactly one actionable number per person.

---

**Q47: How does your app satisfy Rohan's requirement ("complete transparency")?**

Answer: Three things: (1) Every expense shows its full split breakdown. (2) Every imported CSV row that has an anomaly has its raw data stored in `import_anomalies.raw_data` and displayed in the Anomaly Review page. (3) `ImportSession` records every import with total/imported/skipped/anomaly counts. Nothing is silently changed or deleted.

---

**Q48: How does your app satisfy Priya's requirement ("USD conversion")?**

Answer: The `currency` field accepts "USD". `convert_to_inr()` multiplies by ₹83.50 and the result is stored in `amount_inr`. All balance math uses `amount_inr` only. The Expenses page shows both the original amount (e.g., "$45.00") and the INR equivalent ("≈ ₹3757.50") so the user can verify.

---

**Q49: How does your app satisfy Meera's requirement ("duplicates reviewed before deletion")?**

Answer: Duplicate detection sets `action_taken = "pending_review"` and `reviewed = "pending"`. The row is NOT imported. The Anomaly Review page shows all pending anomalies. The user clicks "Approve & Import" or "Reject & Skip". Only after explicit human action does the system take final action. Nothing is auto-deleted.

---

**Q50: What would you improve if you had more time?**

Answer:
1. **Live exchange rates** — Replace the fixed USD rate with a cached call to Open Exchange Rates API.
2. **Alembic migrations** — Instead of `create_all()` in `main.py`, use proper Alembic migration files for every schema change.
3. **Test suite** — pytest unit tests for the balance engine and CSV importer, and integration tests for all API endpoints.
4. **Email notifications** — Notify users when they're added to a group or an expense is created.
5. **Pagination** — The expenses and settlements list endpoints should support `limit` and `offset` for large groups.
6. **httpOnly cookies** — Replace localStorage JWT storage with secure httpOnly cookies for better XSS protection.
