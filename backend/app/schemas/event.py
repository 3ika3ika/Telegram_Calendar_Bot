"""Event schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, field_serializer


class EventBase(BaseModel):
    """Base event schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    start_time: datetime
    end_time: datetime
    timezone: str = Field(default="UTC")
    location: Optional[str] = Field(None, max_length=200)
    extra_metadata: dict = Field(default_factory=dict)
    
    @field_validator("end_time")
    @classmethod
    def validate_end_after_start(cls, v, info):
        """Ensure end_time is after start_time."""
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v


class EventCreate(EventBase):
    """Schema for creating an event."""
    recurrence_rule_id: Optional[int] = None
    reminder_offsets: List[int] = Field(default_factory=list)  # e.g., [15, 60, 1440]


class EventUpdate(BaseModel):
    """Schema for updating an event."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: Optional[str] = None
    location: Optional[str] = Field(None, max_length=200)
    recurrence_rule_id: Optional[int] = None
    reminder_offsets: Optional[List[int]] = None
    extra_metadata: Optional[dict] = None


class EventResponse(EventBase):
    """Schema for event response."""
    id: str
    user_id: int
    team_id: Optional[int] = None
    recurrence_rule_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    @field_serializer('start_time', 'end_time', 'created_at', 'updated_at')
    def serialize_datetime(self, value: datetime, _info) -> str:
        """Serialize datetime to ISO format with Z suffix for UTC."""
        if value.tzinfo is None:
            return value.isoformat() + 'Z'
        return value.isoformat()
    
    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """Schema for event list response."""
    events: List[EventResponse]
    total: int
    page: int
    page_size: int


class EventQueryParams(BaseModel):
    """Query parameters for listing events."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)

