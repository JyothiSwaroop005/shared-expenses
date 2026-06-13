# Shared Expenses App

A full-stack shared expenses tracker built for the Spreetail Software Engineering Internship Assignment.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + Tailwind CSS |
| Backend | FastAPI + SQLAlchemy |
| Database | PostgreSQL (Neon) |
| Deployment | Vercel (frontend) + Render (backend) |

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (local or a free [Neon](https://neon.tech) database)

---

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/shared-expenses.git
cd shared-expenses
```

---

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env file and fill in your values
cp .env.example .env
```

Edit `.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/shared_expenses
SECRET_KEY=your-secret-key-minimum-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
FRONTEND_URL=http://localhost:5173
```

**Create the database (if running locally):**
```bash
psql -U postgres -c "CREATE DATABASE shared_expenses;"
```

**Run the backend:**
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be at: http://localhost:8000  
Docs (Swagger UI): http://localhost:8000/docs

---

### 3. Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Create env file
echo "VITE_API_URL=http://localhost:8000" > .env
```

**Run the frontend:**
```bash
npm run dev
```

The app will be at: http://localhost:5173

---

## CSV Import Format

The CSV file must have these columns:

| Column | Description | Example |
|---|---|---|
| description | Expense name | "Dinner at Olive" |
| amount | Numeric amount | 1200.00 |
| currency | INR or USD | INR |
| paid_by | User's exact name | Aisha |
| group_name | Group's exact name | Goa Trip |
| split_type | equal / percentage / exact | equal |
| expense_date | Date of expense | 2024-01-15 |
| participants | Comma-separated names | Aisha,Rohan,Priya |

**For percentage split:**
```
participants = "Aisha:50,Rohan:30,Priya:20"
```

**For exact split:**
```
participants = "Aisha:600,Rohan:400,Priya:200"
```

---

## Environment Variables

### Backend (.env)

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret (min 32 chars) |
| `ALGORITHM` | JWT algorithm (HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes |
| `FRONTEND_URL` | Allowed CORS origin |

### Frontend (.env)

| Variable | Description |
|---|---|
| `VITE_API_URL` | Backend API base URL |

---

## Deployment

### Backend → Render

1. Push code to GitHub
2. Create new Web Service on [Render](https://render.com)
3. Connect your repo, set root directory to `backend`
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables in Render dashboard

### Frontend → Vercel

1. Push code to GitHub
2. Import project on [Vercel](https://vercel.com)
3. Set root directory to `frontend`
4. Add environment variable: `VITE_API_URL=https://your-render-url.onrender.com`
5. Deploy

### Database → Neon

1. Create account at [neon.tech](https://neon.tech)
2. Create a new project
3. Copy the connection string
4. Use it as `DATABASE_URL` in both Render and local `.env`

---

## Database Migrations (Alembic)

```bash
cd backend

# Generate a new migration after model changes
alembic revision --autogenerate -m "describe your change"

# Apply migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1
```

---

## Project Structure

```
shared-expenses/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app + CORS + router registration
│   │   ├── database.py       # SQLAlchemy engine + session
│   │   ├── models/           # SQLAlchemy ORM models (one per table)
│   │   ├── schemas/          # Pydantic request/response models
│   │   ├── routers/          # FastAPI route handlers (one per feature)
│   │   ├── services/         # Business logic (balance engine, CSV importer)
│   │   └── core/             # Config, security, dependencies
│   ├── alembic/              # Database migrations
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/            # One file per page
│       ├── components/       # Shared UI components
│       ├── api/client.js     # All API calls in one place
│       └── context/          # React Context (auth state)
└── docs/
    ├── SCOPE.md
    ├── DECISIONS.md
    ├── AI_USAGE.md
    └── IMPORT_REPORT_TEMPLATE.md
```
