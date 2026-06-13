from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # These two columns answer Sam's requirement:
    # "I joined later. Earlier expenses should not affect me."
    # joined_at: when they became a member
    # left_at: NULL means they are still in the group
    joined_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    left_at = Column(DateTime(timezone=True), nullable=True)

    # A user can only have one ACTIVE membership per group at a time.
    # We don't use a simple unique constraint on (group_id, user_id) because
    # a user could leave and rejoin - that would create two rows.

    # Relationships
    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="group_memberships")
