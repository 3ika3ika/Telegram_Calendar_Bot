"""Reminder model."""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import ForeignKey


class Reminder(SQLModel, table=True):
    """Reminder for an event."""
    
    __tablename__ = "reminders"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: str = Field(foreign_key="events.id", index=True)
    offset_minutes: int  # minutes before event (e.g., 15, 60, 1440)
    sent_at: Optional[datetime] = None  # when reminder was sent
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    event: "Event" = Relationship(back_populates="reminders")

