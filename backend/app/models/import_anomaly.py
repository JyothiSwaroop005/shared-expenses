from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ImportAnomaly(Base):
    __tablename__ = "import_anomalies"

    id = Column(Integer, primary_key=True, index=True)
    import_session_id = Column(Integer, ForeignKey("import_sessions.id"), nullable=False)

    # Which row in the CSV caused this anomaly (1-indexed, matches Excel row numbers)
    row_number = Column(Integer, nullable=False)

    # Category of anomaly - matches our SCOPE.md definitions
    # Examples: "duplicate_expense", "missing_payer", "invalid_amount"
    anomaly_type = Column(String(100), nullable=False)

    # Human-readable explanation shown in the UI
    description = Column(Text, nullable=False)

    # The raw CSV row data stored as JSON for full traceability (Rohan's requirement)
    raw_data = Column(JSON, nullable=True)

    # What the system did: "skipped" | "imported_with_warning" | "pending_review"
    action_taken = Column(String(100), nullable=False, default="skipped")

    # Meera's requirement: flagged duplicates wait for human review
    # reviewed: has a human looked at this?
    reviewed = Column(String(50), default="pending")  # pending | approved | rejected

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    import_session = relationship("ImportSession", back_populates="anomalies")
