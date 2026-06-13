from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships - these let us do user.group_memberships in Python
    group_memberships = relationship("GroupMember", back_populates="user")
    expenses_paid = relationship("Expense", back_populates="paid_by_user")
    splits = relationship("ExpenseSplit", back_populates="user")
    settlements_paid = relationship("Settlement", foreign_keys="Settlement.payer_id", back_populates="payer")
    settlements_received = relationship("Settlement", foreign_keys="Settlement.payee_id", back_populates="payee")
