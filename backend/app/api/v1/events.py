"""Event endpoints."""
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, List
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
from app.schemas.ai import AIApplyActionRequest, BatchFilters, BatchUpdateFields

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/events", tags=["events"])


def normalize_datetime(dt: datetime) -> datetime:
    """Normalize datetime to UTC timezone-naive for database storage."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        # Convert to UTC and remove timezone info
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    # Already timezone-naive, assume UTC
    return dt


def parse_time_offset(offset_str: str) -> timedelta:
    """
    Parse time offset string like "+1h", "-30m", "+2d" into timedelta.
    
    Examples:
        "+1h" -> timedelta(hours=1)
        "-30m" -> timedelta(minutes=-30)
        "+2d" -> timedelta(days=2)
    """
    if not offset_str:
        return timedelta(0)
    
    # Match pattern: [+-]?[0-9]+[hdms]?
    match = re.match(r'^([+-]?)(\d+)([hdms]?)$', offset_str.strip().lower())
    if not match:
        raise ValueError(f"Invalid time offset format: {offset_str}")
    
    sign, amount, unit = match.groups()
    amount = int(amount)
    if sign == '-':
        amount = -amount
    
    unit_map = {
        'h': 'hours',
        'd': 'days',
        'm': 'minutes',
        's': 'seconds',
        '': 'hours'  # Default to hours if no unit
    }
    
    return timedelta(**{unit_map[unit]: amount})


def build_event_query_from_filters(filters: BatchFilters, user_id: int):
    """Build SQLAlchemy query from batch filters."""
    query = select(Event).where(Event.user_id == user_id)
    
    if filters.date_range_start:
        normalized_start = normalize_datetime(filters.date_range_start)
        query = query.where(Event.start_time >= normalized_start)
    
    if filters.date_range_end:
        normalized_end = normalize_datetime(filters.date_range_end)
        query = query.where(Event.end_time <= normalized_end)
    
    if filters.title_pattern:
        query = query.where(Event.title.ilike(f"%{filters.title_pattern}%"))
    
    if filters.event_ids:
        query = query.where(Event.id.in_(filters.event_ids))
    
    if filters.recurrence_rule_id is not None:
        query = query.where(Event.recurrence_rule_id == filters.recurrence_rule_id)
    
    # Tags would need to be stored in extra_metadata, so we'd query that
    # For now, we'll skip tag filtering as it requires schema changes
    
    return query


def event_to_response(event: Event) -> EventResponse:
    """Convert Event model to EventResponse schema, mapping extra_metadata to metadata."""
    # Get extra_metadata, defaulting to empty dict if None
    extra_metadata = getattr(event, 'extra_metadata', None)
    if extra_metadata is None:
        extra_metadata = {}
    
    # Ensure datetimes are timezone-aware (UTC) for proper JSON serialization
    # Database stores UTC as timezone-naive, so we add UTC timezone info
    start_time = event.start_time
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    
    end_time = event.end_time
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    
    created_at = getattr(event, 'created_at', datetime.utcnow())
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    
    updated_at = getattr(event, 'updated_at', datetime.utcnow())
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    
    event_dict = {
        'id': str(event.id),
        'user_id': int(event.user_id),
        'team_id': getattr(event, 'team_id', None),
        'title': str(event.title),
        'description': getattr(event, 'description', None),
        'start_time': start_time,
        'end_time': end_time,
        'timezone': str(getattr(event, 'timezone', 'UTC')),
        'location': getattr(event, 'location', None),
        'recurrence_rule_id': getattr(event, 'recurrence_rule_id', None),
        'created_at': created_at,
        'updated_at': updated_at,
        'metadata': extra_metadata,
    }
    return EventResponse.model_validate(event_dict)


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
    # Normalize timezone-aware datetimes to UTC timezone-naive for database
    normalized_start = normalize_datetime(event_data.start_time)
    normalized_end = normalize_datetime(event_data.end_time)
    
    # Prevent creating events in the past
    # Allow a small buffer (5 minutes) to account for timezone differences and clock skew
    now = datetime.utcnow()
    buffer = timedelta(minutes=5)
    if normalized_start < (now - buffer):
        raise HTTPException(
            status_code=400, 
            detail="You cannot create events in the past"
        )
    # Check for duplicates (same title and overlapping time)
    # Only check if title is provided and times overlap
    if event_data.title:
        existing = await session.execute(
            select(Event).where(
                and_(
                    Event.user_id == user_id,
                    Event.title == event_data.title,
                    Event.start_time < normalized_end,
                    Event.end_time > normalized_start,
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
        start_time=normalized_start,
        end_time=normalized_end,
        timezone=event_data.timezone,
        location=event_data.location,
        recurrence_rule_id=event_data.recurrence_rule_id,
        extra_metadata=event_data.metadata or {},
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
        extra_metadata={"title": event.title},
    )
    session.add(audit)
    
    await session.commit()
    await session.refresh(event)
    
    return event_to_response(event)


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
    
    # Normalize datetime query parameters to timezone-naive UTC
    if start_date:
        normalized_start = normalize_datetime(start_date)
        query = query.where(Event.start_time >= normalized_start)
    if end_date:
        normalized_end = normalize_datetime(end_date)
        query = query.where(Event.end_time <= normalized_end)
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
        events=[event_to_response(e) for e in events],
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
    return event_to_response(event)


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
    
    # Store original values for duplicate checking
    original_start = event.start_time
    original_end = event.end_time
    original_title = event.title
    
    # Update fields
    if event_update.title is not None:
        event.title = event_update.title
    if event_update.description is not None:
        event.description = event_update.description
    if event_update.start_time is not None:
        event.start_time = normalize_datetime(event_update.start_time)
    if event_update.end_time is not None:
        event.end_time = normalize_datetime(event_update.end_time)
    if event_update.timezone is not None:
        event.timezone = event_update.timezone
    if event_update.location is not None:
        event.location = event_update.location
    if event_update.recurrence_rule_id is not None:
        event.recurrence_rule_id = event_update.recurrence_rule_id
    if event_update.metadata is not None:
        if event.extra_metadata is None:
            event.extra_metadata = {}
        event.extra_metadata.update(event_update.metadata)
    
    # Check for duplicates only if title or time changed to a value that conflicts
    # Skip if only updating other fields (description, location, etc.)
    title_changed = event_update.title is not None and event.title != original_title
    time_changed = (event_update.start_time is not None or event_update.end_time is not None) and \
                   (event.start_time != original_start or event.end_time != original_end)
    
    if title_changed or time_changed:
        # Check for duplicates with new title/time (excluding current event)
        existing = await session.execute(
            select(Event).where(
                and_(
                    Event.user_id == user_id,
                    Event.id != event_id,  # Exclude the event being updated
                    Event.title == event.title,
                    Event.start_time < event.end_time,
                    Event.end_time > event.start_time,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Duplicate event detected")
    
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
        extra_metadata={"title": event.title},
    )
    session.add(audit)
    
    await session.commit()
    await session.refresh(event)
    
    return event_to_response(event)


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
        extra_metadata={"title": event.title},
    )
    session.add(audit)
    
    await session.delete(event)
    await session.commit()
    
    return None


@router.post("/apply_action")
async def apply_ai_action(
    action_request: AIApplyActionRequest,
    user_id: int = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
):
    """
    Apply an AI-generated action.
    
    This endpoint validates and applies actions from AI parsing.
    It enforces global rules (e.g., MOVE = CREATE + DELETE).
    
    Returns EventResponse for single-event actions, or a summary dict for batch operations.
    """
    action = action_request.action
    payload = action_request.payload
    
    if action == "CREATE":
        if not payload.title or not payload.start_time or not payload.end_time:
            raise HTTPException(status_code=400, detail="CREATE action requires title, start_time, and end_time")
        
        event_data = EventCreate(
            title=payload.title,
            description=payload.description or payload.message,
            start_time=payload.start_time,
            end_time=payload.end_time,
            location=payload.location,
            reminder_offsets=payload.reminders or [],
        )
        created_event = await create_event(event_data, user_id, session)
        
        # Add notes and tags to metadata if provided
        if payload.notes or payload.tags:
            result = await session.execute(
                select(Event).where(Event.id == created_event.id)
            )
            event = result.scalar_one_or_none()
            if event:
                if event.extra_metadata is None:
                    event.extra_metadata = {}
                if payload.notes:
                    event.extra_metadata["notes"] = payload.notes
                if payload.tags:
                    event.extra_metadata["tags"] = payload.tags
                await session.commit()
                await session.refresh(event)
                return event_to_response(event)
        
        return created_event
    
    elif action == "UPDATE":
        if not payload.event_id:
            raise HTTPException(status_code=400, detail="UPDATE action requires event_id")
        
        update_data = EventUpdate()
        if payload.title:
            update_data.title = payload.title
        if payload.description:
            update_data.description = payload.description
        if payload.start_time:
            update_data.start_time = payload.start_time
        if payload.end_time:
            update_data.end_time = payload.end_time
        if payload.location:
            update_data.location = payload.location
        if payload.reminders:
            update_data.reminder_offsets = payload.reminders
        
        # Handle notes and tags in metadata
        metadata_updates = {}
        if payload.notes:
            metadata_updates["notes"] = payload.notes
        if payload.tags:
            metadata_updates["tags"] = payload.tags
        if metadata_updates:
            update_data.metadata = metadata_updates
        
        return await update_event(payload.event_id, update_data, user_id, session)
    
    elif action == "DELETE":
        if not payload.event_id:
            raise HTTPException(status_code=400, detail="DELETE action requires event_id")
        
        # Get event info before deleting
        result = await session.execute(
            select(Event).where(
                and_(Event.id == payload.event_id, Event.user_id == user_id)
            )
        )
        event = result.scalar_one_or_none()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Store event info for response
        event_info = event_to_response(event)
        
        # Delete the event
        await delete_event(payload.event_id, user_id, session)
        
        # Return the deleted event info
        return event_info
    
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
            extra_metadata={
                "original_id": payload.event_id,
                "new_id": new_event.id,
                "title": original_event.title,
            },
        )
        session.add(audit)
        await session.commit()
        
        return new_event
    
    elif action == "DUPLICATE":
        if not payload.event_id:
            raise HTTPException(status_code=400, detail="DUPLICATE action requires event_id")
        
        # Get original event
        result = await session.execute(
            select(Event).where(
                and_(Event.id == payload.event_id, Event.user_id == user_id)
            )
        )
        original_event = result.scalar_one_or_none()
        if not original_event:
            raise HTTPException(status_code=404, detail="Event to duplicate not found")
        
        # Use new times if provided, otherwise use original times
        new_start = payload.start_time if payload.start_time else original_event.start_time
        new_end = payload.end_time if payload.end_time else original_event.end_time
        
        # Create duplicate event
        duplicate_data = EventCreate(
            title=payload.title or f"{original_event.title} (copy)",
            description=payload.description or original_event.description,
            start_time=new_start,
            end_time=new_end,
            timezone=original_event.timezone,
            location=payload.location or original_event.location,
            reminder_offsets=payload.reminders or [],
        )
        duplicate_event = await create_event(duplicate_data, user_id, session)
        
        # Audit log
        audit = AuditLog(
            user_id=user_id,
            action="DUPLICATE",
            resource_type="event",
            resource_id=original_event.id,
            extra_metadata={
                "original_id": original_event.id,
                "duplicate_id": duplicate_event.id,
                "title": original_event.title,
            },
        )
        session.add(audit)
        await session.commit()
        
        return duplicate_event
    
    elif action == "BATCH_UPDATE":
        if not payload.filters or not payload.update_fields:
            raise HTTPException(status_code=400, detail="BATCH_UPDATE requires filters and update_fields")
        
        # Build query from filters
        query = build_event_query_from_filters(payload.filters, user_id)
        result = await session.execute(query)
        events_to_update = result.scalars().all()
        
        if not events_to_update:
            raise HTTPException(status_code=404, detail="No events found matching filters")
        
        updated_count = 0
        update_fields = payload.update_fields
        
        for event in events_to_update:
            # Update basic fields
            if update_fields.title is not None:
                event.title = update_fields.title
            if update_fields.description is not None:
                event.description = update_fields.description
            if update_fields.location is not None:
                event.location = update_fields.location
            
            # Handle time offsets
            if update_fields.start_time_offset:
                offset = parse_time_offset(update_fields.start_time_offset)
                event.start_time = event.start_time + offset
            if update_fields.end_time_offset:
                offset = parse_time_offset(update_fields.end_time_offset)
                event.end_time = event.end_time + offset
            
            # Update reminders if provided
            if update_fields.reminders is not None:
                # Delete existing reminders
                result_reminders = await session.execute(
                    select(Reminder).where(Reminder.event_id == event.id)
                )
                for reminder in result_reminders.scalars():
                    await session.delete(reminder)
                
                # Create new reminders
                for offset_minutes in update_fields.reminders:
                    reminder = Reminder(
                        event_id=event.id,
                        offset_minutes=offset_minutes,
                    )
                    session.add(reminder)
            
            # Update tags in metadata (if supported)
            if update_fields.tags is not None:
                if event.extra_metadata is None:
                    event.extra_metadata = {}
                event.extra_metadata["tags"] = update_fields.tags
            
            event.updated_at = datetime.utcnow()
            updated_count += 1
            
            # Audit log for each update
            audit = AuditLog(
                user_id=user_id,
                action="BATCH_UPDATE",
                resource_type="event",
                resource_id=event.id,
                extra_metadata={"title": event.title, "batch": True},
            )
            session.add(audit)
        
        await session.commit()
        
        # Return the first updated event as representative
        if events_to_update:
            await session.refresh(events_to_update[0])
            response = event_to_response(events_to_update[0])
            # Add metadata about batch operation
            response.metadata["batch_count"] = updated_count
            return response
        else:
            raise HTTPException(status_code=404, detail="No events updated")
    
    elif action == "BATCH_DELETE":
        if not payload.filters:
            raise HTTPException(status_code=400, detail="BATCH_DELETE requires filters")
        
        # Build query from filters
        query = build_event_query_from_filters(payload.filters, user_id)
        result = await session.execute(query)
        events_to_delete = result.scalars().all()
        
        if not events_to_delete:
            raise HTTPException(status_code=404, detail="No events found matching filters")
        
        deleted_count = 0
        deleted_titles = []
        first_event_data = None  # Store first event data before deletion
        
        for event in events_to_delete:
            deleted_titles.append(event.title)
            
            # Store first event data before deletion
            if first_event_data is None:
                first_event_data = {
                    "id": event.id,
                    "start_time": event.start_time,
                    "end_time": event.end_time,
                    "timezone": event.timezone,
                }
            
            # Audit log before deletion
            audit = AuditLog(
                user_id=user_id,
                action="BATCH_DELETE",
                resource_type="event",
                resource_id=event.id,
                extra_metadata={"title": event.title, "batch": True},
            )
            session.add(audit)
            
            await session.delete(event)
            deleted_count += 1
        
        await session.commit()
        
        # For batch delete, return a summary response
        if deleted_count > 0 and first_event_data:
            summary_dict = {
                "id": first_event_data["id"],
                "user_id": user_id,
                "title": f"Batch delete: {deleted_count} events",
                "description": f"Deleted {deleted_count} events: {', '.join(deleted_titles[:5])}",
                "start_time": first_event_data["start_time"].replace(tzinfo=timezone.utc) if first_event_data["start_time"] else datetime.utcnow().replace(tzinfo=timezone.utc),
                "end_time": first_event_data["end_time"].replace(tzinfo=timezone.utc) if first_event_data["end_time"] else datetime.utcnow().replace(tzinfo=timezone.utc),
                "timezone": first_event_data["timezone"] or "UTC",
                "created_at": datetime.utcnow().replace(tzinfo=timezone.utc),
                "updated_at": datetime.utcnow().replace(tzinfo=timezone.utc),
                "metadata": {
                    "batch_deleted": True,
                    "deleted_count": deleted_count,
                    "deleted_titles": deleted_titles[:10],  # First 10 titles
                }
            }
            return EventResponse.model_validate(summary_dict)
        else:
            raise HTTPException(status_code=404, detail="No events deleted")
    
    else:
        raise HTTPException(status_code=400, detail=f"Action {action} not supported for direct application")

