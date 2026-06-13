from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# The engine is the connection to the database.
# pool_pre_ping=True means SQLAlchemy will test the connection before using it.
# This handles Neon's serverless connection drops gracefully.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    # Neon free tier has connection limits - keep the pool small
    pool_size=5,
    max_overflow=10,
)

# SessionLocal is a factory: calling SessionLocal() gives you a new DB session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class for all SQLAlchemy models.
# When a model inherits from Base, SQLAlchemy knows it maps to a DB table.
Base = declarative_base()
