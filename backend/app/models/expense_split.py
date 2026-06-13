from sqlalchemy import Column, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class ExpenseSplit(Base):
    __tablename__ = "expense_splits"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # The exact amount this person owes for this expense (in INR)
    # This is pre-calculated and stored - don't recalculate at query time
    # For equal split: amount_inr / num_participants
    # For percentage split: (percentage / 100) * amount_inr
    # For exact split: the explicit amount from the CSV or form
    owed_amount = Column(Numeric(10, 2), nullable=False)

    # Relationships
    expense = relationship("Expense", back_populates="splits")
    user = relationship("User", back_populates="splits")
