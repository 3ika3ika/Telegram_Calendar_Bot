"""AI parsing schemas."""
from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class AIParseRequest(BaseModel):
    """Request schema for AI parsing."""
    text: str = Field(..., min_length=1, max_length=1000)
    context_events: Optional[List[dict]] = None  # Recent events for context
    user_memory: Optional[dict] = None  # User preferences/memory


class BatchFilters(BaseModel):
    """Filters for batch operations."""
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    title_pattern: Optional[str] = None  # For title matching
    tags: Optional[List[str]] = None
    recurrence_rule_id: Optional[int] = None
    event_ids: Optional[List[str]] = None  # Specific event IDs


class BatchUpdateFields(BaseModel):
    """Fields to update in batch operations."""
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start_time_offset: Optional[str] = None  # e.g., "+1h", "-30m", "+1d"
    end_time_offset: Optional[str] = None
    reminders: Optional[List[int]] = None
    tags: Optional[List[str]] = None


class AIActionPayload(BaseModel):
    """Payload for AI action."""
    # Single event operations
    event_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    recurrence: Optional[dict] = None
    reminders: Optional[List[int]] = None  # offset minutes
    location: Optional[str] = None
    notes: Optional[str] = None  # Additional notes
    tags: Optional[List[str]] = None
    
    # Batch operations
    filters: Optional[BatchFilters] = None
    update_fields: Optional[BatchUpdateFields] = None
    
    # Human-readable message
    message: Optional[str] = None


class AIActionResponse(BaseModel):
    """Response schema for AI parsing."""
    action: Literal[
        "CREATE", "UPDATE", "DELETE", "MOVE", "DUPLICATE",
        "BATCH_UPDATE", "BATCH_DELETE",
        "SUGGEST", "ASK", "NOOP", "CONFLICT"
    ]
    payload: AIActionPayload
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    summary: str  # Human-readable summary


class AIApplyActionRequest(BaseModel):
    """Request to apply an AI-generated action."""
    action: Literal[
        "CREATE", "UPDATE", "DELETE", "MOVE", "DUPLICATE",
        "BATCH_UPDATE", "BATCH_DELETE",
        "SUGGEST", "ASK", "NOOP", "CONFLICT"
    ]
    payload: AIActionPayload
    original_text: Optional[str] = None  # Original user input for audit

