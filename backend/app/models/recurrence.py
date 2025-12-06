"""Recurrence rule model."""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship


class RecurrenceRule(SQLModel, table=True):
    """Recurrence rule for recurring events."""
    
    __tablename__ = "recurrencerules"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    frequency: str  # daily, weekly, monthly, yearly, custom
    interval: int = Field(default=1)  # every N days/weeks/etc
    by_day: Optional[str] = None  # comma-separated: "MO,WE,FR" for weekly
    by_month_day: Optional[str] = None  # comma-separated: "1,15" for monthly
    by_month: Optional[str] = None  # comma-separated: "1,6" for yearly
    end_date: Optional[datetime] = None  # when recurrence ends
    count: Optional[int] = None  # max occurrences
    rrule_string: Optional[str] = None  # full RRULE string if custom
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    events: list["Event"] = Relationship(back_populates="recurrence_rule")

