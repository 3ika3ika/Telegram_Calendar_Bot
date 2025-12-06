"""AI parsing schemas."""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class AIParseRequest(BaseModel):
    """Request schema for AI parsing."""
    text: str = Field(..., min_length=1, max_length=1000)
    context_events: Optional[List[dict]] = None  # Recent events for context
    user_memory: Optional[dict] = None  # User preferences/memory


class AIActionPayload(BaseModel):
    """Payload for AI action."""
    event_id: Optional[str] = None
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    recurrence: Optional[dict] = None
    reminders: Optional[List[int]] = None  # offset minutes
    message: Optional[str] = None  # Human-readable message


class AIActionResponse(BaseModel):
    """Response schema for AI parsing."""
    action: Literal["CREATE", "UPDATE", "DELETE", "MOVE", "SUGGEST", "ASK", "NOOP", "CONFLICT"]
    payload: AIActionPayload
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    summary: str  # Human-readable summary


class AIApplyActionRequest(BaseModel):
    """Request to apply an AI-generated action."""
    action: Literal["CREATE", "UPDATE", "DELETE", "MOVE", "SUGGEST", "ASK", "NOOP", "CONFLICT"]
    payload: AIActionPayload
    original_text: Optional[str] = None  # Original user input for audit

