from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class SplitType(str, enum.Enum):
    EQUAL = "equal"
    PERCENTAGE = "percentage"
    EXACT = "exact"


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)

    # Who physically paid the bill (not who owes money)
    paid_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    description = Column(String(500), nullable=False)

    # Numeric(10, 2) = up to 10 digits total, 2 after decimal point
    # Never use Float for money - floating point errors compound
    amount = Column(Numeric(10, 2), nullable=False)

    currency = Column(String(3), default="INR", nullable=False)

    # amount_inr stores the converted amount in INR for consistent balance calculation
    # If currency is INR, amount_inr == amount
    amount_inr = Column(Numeric(10, 2), nullable=False)

    split_type = Column(Enum(SplitType), nullable=False, default=SplitType.EQUAL)

    # The date the expense actually occurred (not when it was entered)
    expense_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Notes for audit trail - used by importer to flag anomalies
    notes = Column(Text, nullable=True)

    # Track if this came from a CSV import
    import_session_id = Column(Integer, ForeignKey("import_sessions.id"), nullable=True)

    # Relationships
    group = relationship("Group", back_populates="expenses")
    paid_by_user = relationship("User", back_populates="expenses_paid")
    splits = relationship("ExpenseSplit", back_populates="expense", cascade="all, delete-orphan")
    import_session = relationship("ImportSession", back_populates="expenses")
