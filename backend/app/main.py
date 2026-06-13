from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database import engine, Base

# Import all models so SQLAlchemy registers them before create_all
import app.models  # noqa: F401

from app.routers import auth, groups, expenses, settlements, balances, imports, anomalies

# Create all tables if they don't exist.
# In production with Alembic, you'd use migrations instead.
# For local dev this is convenient.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Shared Expenses API",
    description="Backend for the Spreetail Shared Expenses App",
    version="1.0.0",
)

# CORS: allow the frontend to call this API
# In production, replace "*" with your actual Vercel URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(auth.router)
app.include_router(groups.router)
app.include_router(expenses.router)
app.include_router(settlements.router)
app.include_router(balances.router)
app.include_router(imports.router)
app.include_router(anomalies.router)


@app.get("/")
def health_check():
    """Simple health check endpoint - confirms the API is running."""
    return {"status": "ok", "message": "Shared Expenses API is running"}
