# Git Commit Plan

A realistic sequence of 28 commits representing how this project was built incrementally.

```bash
# 1 - Project scaffold
git commit -m "chore: initialize project structure with backend and frontend folders"

# 2 - Database setup
git commit -m "feat: add SQLAlchemy engine, session factory, and Base in database.py"

# 3 - Core config
git commit -m "feat: add pydantic-settings config and JWT security utilities"

# 4 - User model and schema
git commit -m "feat: add User SQLAlchemy model and Pydantic schemas"

# 5 - Group models
git commit -m "feat: add Group and GroupMember models with joined_at and left_at timestamps"

# 6 - Expense models
git commit -m "feat: add Expense model with SplitType enum and amount_inr for currency normalization"

# 7 - Split and settlement models
git commit -m "feat: add ExpenseSplit and Settlement models"

# 8 - Import tracking models
git commit -m "feat: add ImportSession and ImportAnomaly models for CSV traceability"

# 9 - Alembic setup
git commit -m "chore: configure Alembic for database migrations"

# 10 - Auth endpoints
git commit -m "feat: add /auth/signup and /auth/login endpoints with bcrypt and JWT"

# 11 - Auth dependency
git commit -m "feat: add get_current_user dependency for protected route authentication"

# 12 - Groups API
git commit -m "feat: add groups CRUD endpoints with member add/remove support"

# 13 - Currency service
git commit -m "feat: add currency conversion service with fixed USD to INR rate"

# 14 - Balance engine - split calculation
git commit -m "feat: implement equal, percentage, and exact split calculation with Decimal precision"

# 15 - Balance engine - net balances
git commit -m "feat: implement get_group_balances with membership date window checks"

# 16 - Debt simplification
git commit -m "feat: implement greedy debt simplification algorithm for minimum transactions"

# 17 - Expenses API
git commit -m "feat: add expense creation endpoint with split calculation and currency conversion"

# 18 - Settlements API
git commit -m "feat: add settlement recording and listing endpoints"

# 19 - Balances API
git commit -m "feat: add group balances and personal summary endpoints"

# 20 - CSV importer core
git commit -m "feat: add CSV importer with pandas parsing and column validation"

# 21 - Anomaly detection
git commit -m "feat: implement 18 anomaly types in CSV importer with blocking and non-blocking classification"

# 22 - Import and anomaly APIs
git commit -m "feat: add CSV upload endpoint and anomaly review endpoints"

# 23 - FastAPI app assembly
git commit -m "feat: assemble FastAPI app with CORS middleware and all routers"

# 24 - Frontend scaffold
git commit -m "chore: initialize React + Vite + Tailwind frontend"

# 25 - Auth context and routing
git commit -m "feat: add AuthContext, ProtectedRoute, and React Router setup"

# 26 - Core pages
git commit -m "feat: add Login, Dashboard, Groups, and GroupDetail pages"

# 27 - Expense and settlement pages
git commit -m "feat: add Expenses page with all three split types and Settlements page"

# 28 - Import and anomaly pages
git commit -m "feat: add ImportCSV page with report display and AnomalyReview page"

# 29 - Balances page
git commit -m "feat: add Balances page with simplified and raw balance views"

# 30 - Documentation
git commit -m "docs: add README, SCOPE.md, DECISIONS.md, AI_USAGE.md, and IMPORT_REPORT_TEMPLATE.md"
```

## How to use this plan

Follow these commits in order as you build the project. Each commit should only contain the files relevant to that feature. This demonstrates:

1. You built incrementally (not all at once)
2. You thought about what to commit and why
3. Commit messages are meaningful and follow conventional commit format (`feat:`, `chore:`, `docs:`, `fix:`)

## Conventional commit prefixes

| Prefix | When to use |
|---|---|
| `feat:` | New feature or endpoint |
| `fix:` | Bug fix |
| `chore:` | Config, dependencies, scaffolding |
| `docs:` | Documentation only |
| `refactor:` | Code restructure without behavior change |
| `test:` | Adding tests |
