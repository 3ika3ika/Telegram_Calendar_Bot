"""Event endpoints."""
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from app.db.session import get_session
from app.models.event import Event
from app.models.reminder import Reminder
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.event import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventListResponse,
    EventQueryParams,
)
from app.schemas.ai import AIApplyActionRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/events", tags=["events"])


def get_user_id(telegram_user_id: int = Header(..., alias="X-Telegram-User-Id")) -> int:
    """Dependency to extract telegram_user_id from header."""
    return telegram_user_id


@router.post("", response_model=EventResponse, status_code=201)
async def create_event(
    event_data: EventCreate,
    user_id: int = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Create a new event."""
    # Check for duplicates (same title and overlapping time)
    existing = await session.execute(
        select(Event).where(
            and_(
                Event.user_id == user_id,
                Event.title == event_data.title,
                Event.start_time < event_data.end_time,
                Event.end_time > event_data.start_time,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Duplicate event detected")
    
    # Create event
    event = Event(
        user_id=user_id,
        title=event_data.title,
        description=event_data.description,
        start_time=event_data.start_time,
        end_time=event_data.end_time,
        timezone=event_data.timezone,
        location=event_data.location,
        recurrence_rule_id=event_data.recurrence_rule_id,
        metadata=event_data.metadata,
    )
    session.add(event)
    await session.flush()
    
    # Create reminders
    for offset in event_data.reminder_offsets:
        reminder = Reminder(
            event_id=event.id,
            offset_minutes=offset,
        )
        session.add(reminder)
    
    # Audit log
    audit = AuditLog(
        user_id=user_id,
        action="CREATE",
        resource_type="event",
        resource_id=event.id,
        metadata={"title": event.title},
    )
    session.add(audit)
    
    await session.commit()
    await session.refresh(event)
    
    return EventResponse.model_validate(event)


@router.get("", response_model=EventListResponse)
async def list_events(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: int = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
):
    """List events with filters."""
    query = select(Event).where(Event.user_id == user_id)
    
    if start_date:
        query = query.where(Event.start_time >= start_date)
    if end_date:
        query = query.where(Event.end_time <= end_date)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Event.title.ilike(search_term),
                Event.description.ilike(search_term),
                Event.location.ilike(search_term),
            )
        )
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar()
    
    # Paginate
    query = query.order_by(Event.start_time).offset((page - 1) * page_size).limit(page_size)
    
    result = await session.execute(query)
    events = result.scalars().all()
    
    return EventListResponse(
        events=[EventResponse.model_validate(e) for e in events],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    user_id: int = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Get a specific event."""
    result = await session.execute(
        select(Event).where(
            and_(Event.id == event_id, Event.user_id == user_id)
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventResponse.model_validate(event)


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    event_update: EventUpdate,
    user_id: int = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Update an event."""
    result = await session.execute(
        select(Event).where(
            and_(Event.id == event_id, Event.user_id == user_id)
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Update fields
    if event_update.title is not None:
        event.title = event_update.title
    if event_update.description is not None:
        event.description = event_update.description
    if event_update.start_time is not None:
        event.start_time = event_update.start_time
    if event_update.end_time is not None:
        event.end_time = event_update.end_time
    if event_update.timezone is not None:
        event.timezone = event_update.timezone
    if event_update.location is not None:
        event.location = event_update.location
    if event_update.recurrence_rule_id is not None:
        event.recurrence_rule_id = event_update.recurrence_rule_id
    if event_update.metadata is not None:
        event.metadata.update(event_update.metadata)
    
    event.updated_at = datetime.utcnow()
    
    # Update reminders if provided
    if event_update.reminder_offsets is not None:
        # Delete existing reminders
        result_reminders = await session.execute(
            select(Reminder).where(Reminder.event_id == event_id)
        )
        for reminder in result_reminders.scalars():
            await session.delete(reminder)
        
        # Create new reminders
        for offset in event_update.reminder_offsets:
            reminder = Reminder(
                event_id=event.id,
                offset_minutes=offset,
            )
            session.add(reminder)
    
    # Audit log
    audit = AuditLog(
        user_id=user_id,
        action="UPDATE",
        resource_type="event",
        resource_id=event.id,
        metadata={"title": event.title},
    )
    session.add(audit)
    
    await session.commit()
    await session.refresh(event)
    
    return EventResponse.model_validate(event)


@router.delete("/{event_id}", status_code=204)
async def delete_event(
    event_id: str,
    user_id: int = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Delete an event."""
    result = await session.execute(
        select(Event).where(
            and_(Event.id == event_id, Event.user_id == user_id)
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Audit log
    audit = AuditLog(
        user_id=user_id,
        action="DELETE",
        resource_type="event",
        resource_id=event.id,
        metadata={"title": event.title},
    )
    session.add(audit)
    
    await session.delete(event)
    await session.commit()
    
    return None


@router.post("/apply_action", response_model=EventResponse)
async def apply_ai_action(
    action_request: AIApplyActionRequest,
    user_id: int = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
):
    """
    Apply an AI-generated action.
    
    This endpoint validates and applies actions from AI parsing.
    It enforces global rules (e.g., MOVE = CREATE + DELETE).
    """
    action = action_request.action
    payload = action_request.payload
    
    if action == "CREATE":
        if not payload.title or not payload.start_time or not payload.end_time:
            raise HTTPException(status_code=400, detail="CREATE action requires title, start_time, and end_time")
        
        event_data = EventCreate(
            title=payload.title,
            description=payload.message,
            start_time=payload.start_time,
            end_time=payload.end_time,
            reminder_offsets=payload.reminders or [],
        )
        return await create_event(event_data, user_id, session)
    
    elif action == "UPDATE":
        if not payload.event_id:
            raise HTTPException(status_code=400, detail="UPDATE action requires event_id")
        
        update_data = EventUpdate()
        if payload.title:
            update_data.title = payload.title
        if payload.start_time:
            update_data.start_time = payload.start_time
        if payload.end_time:
            update_data.end_time = payload.end_time
        if payload.reminders:
            update_data.reminder_offsets = payload.reminders
        
        return await update_event(payload.event_id, update_data, user_id, session)
    
    elif action == "DELETE":
        if not payload.event_id:
            raise HTTPException(status_code=400, detail="DELETE action requires event_id")
        
        await delete_event(payload.event_id, user_id, session)
        # Return a placeholder response
        return EventResponse(
            id=payload.event_id,
            user_id=user_id,
            title="",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            timezone="UTC",
        )
    
    elif action == "MOVE":  # Special handling: CREATE + DELETE
        if not payload.event_id:
            raise HTTPException(status_code=400, detail="MOVE action requires event_id")
        if not payload.start_time or not payload.end_time:
            raise HTTPException(status_code=400, detail="MOVE action requires start_time and end_time")
        
        # Get original event
        result = await session.execute(
            select(Event).where(
                and_(Event.id == payload.event_id, Event.user_id == user_id)
            )
        )
        original_event = result.scalar_one_or_none()
        if not original_event:
            raise HTTPException(status_code=404, detail="Event to move not found")
        
        # Create new event
        new_event_data = EventCreate(
            title=original_event.title,
            description=original_event.description,
            start_time=payload.start_time,
            end_time=payload.end_time,
            timezone=original_event.timezone,
            location=original_event.location,
            reminder_offsets=payload.reminders or [],
        )
        new_event = await create_event(new_event_data, user_id, session)
        
        # Delete original event
        await delete_event(payload.event_id, user_id, session)
        
        # Audit log
        audit = AuditLog(
            user_id=user_id,
            action="MOVE",
            resource_type="event",
            resource_id=payload.event_id,
            metadata={
                "original_id": payload.event_id,
                "new_id": new_event.id,
                "title": original_event.title,
            },
        )
        session.add(audit)
        await session.commit()
        
        return new_event
    
    else:
        raise HTTPException(status_code=400, detail=f"Action {action} not supported for direct application")

