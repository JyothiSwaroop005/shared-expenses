from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ImportSession(Base):
    __tablename__ = "import_sessions"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Counters for the import report
    total_rows = Column(Integer, default=0)
    imported_rows = Column(Integer, default=0)
    skipped_rows = Column(Integer, default=0)
    anomaly_count = Column(Integer, default=0)

    # Status: pending | completed | failed
    status = Column(String(50), default="pending")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])
    anomalies = relationship("ImportAnomaly", back_populates="import_session")
    expenses = relationship("Expense", back_populates="import_session")
