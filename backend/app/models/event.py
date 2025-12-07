"""Event model."""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, JSON, Relationship
from sqlalchemy import BigInteger, ForeignKey, Index
import uuid


class Event(SQLModel, table=True):
    """Event model representing a calendar event."""
    
    __tablename__ = "events"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: int = Field(sa_column=Column(BigInteger, ForeignKey("users.telegram_user_id"), index=True))
    team_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, index=True))
    title: str
    description: Optional[str] = None
    start_time: datetime = Field(index=True)
    end_time: datetime = Field(index=True)
    timezone: str = Field(default="UTC")
    location: Optional[str] = None
    recurrence_rule_id: Optional[int] = Field(default=None, foreign_key="recurrencerules.id")
    extra_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    recurrence_rule: Optional["RecurrenceRule"] = Relationship(back_populates="events")
    reminders: list["Reminder"] = Relationship(back_populates="event")
    
    __table_args__ = (
        Index("idx_user_start_time", "user_id", "start_time"),
        Index("idx_user_end_time", "user_id", "end_time"),
    )

