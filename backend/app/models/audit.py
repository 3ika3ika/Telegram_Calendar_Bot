"""Audit log model."""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, JSON
from sqlalchemy import BigInteger, Index


class AuditLog(SQLModel, table=True):
    """Audit log for tracking important actions."""
    
    __tablename__ = "audit_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(sa_column=Column(BigInteger, index=True))
    action: str  # CREATE, UPDATE, DELETE, MOVE, etc.
    resource_type: str  # event, reminder, user, etc.
    resource_id: str
    metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_user_created", "user_id", "created_at"),
    )

