"""AI parsing logic with server-side validation."""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.ai.engine import ai_engine, MASTER_SYSTEM_PROMPT
from app.schemas.ai import AIActionResponse, AIActionPayload

logger = logging.getLogger(__name__)


def normalize_datetime_for_comparison(dt: datetime) -> datetime:
    """Normalize datetime to UTC timezone-naive for comparison."""
    if dt.tzinfo is not None:
        # Convert to UTC and remove timezone info
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    # Already timezone-naive, assume UTC
    return dt

# Allowed actions
ALLOWED_ACTIONS = {"CREATE", "UPDATE", "DELETE", "MOVE", "SUGGEST", "ASK", "NOOP", "CONFLICT"}


def validate_ai_action(action_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate AI action against global rules and schema.
    
    Args:
        action_data: Parsed action from AI
        
    Returns:
        (is_valid, error_message)
    """
    # Check action is allowed
    action = action_data.get("action")
    if action not in ALLOWED_ACTIONS:
        return False, f"Invalid action: {action}"
    
    payload = action_data.get("payload", {})
    
    # Validate based on action type
    if action == "CREATE":
        if not payload.get("title"):
            return False, "CREATE action requires title"
        if not payload.get("start_time"):
            return False, "CREATE action requires start_time"
        if not payload.get("end_time"):
            return False, "CREATE action requires end_time"
        # Validate times
        try:
            start = datetime.fromisoformat(payload["start_time"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(payload["end_time"].replace("Z", "+00:00"))
            if end <= start:
                return False, "end_time must be after start_time"
        except (ValueError, AttributeError) as e:
            return False, f"Invalid datetime format: {e}"
    
    elif action == "UPDATE":
        if not payload.get("event_id"):
            return False, "UPDATE action requires event_id"
        # Validate times if provided
        if payload.get("start_time") and payload.get("end_time"):
            try:
                start = datetime.fromisoformat(payload["start_time"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(payload["end_time"].replace("Z", "+00:00"))
                if end <= start:
                    return False, "end_time must be after start_time"
            except (ValueError, AttributeError) as e:
                return False, f"Invalid datetime format: {e}"
    
    elif action == "DELETE":
        if not payload.get("event_id"):
            return False, "DELETE action requires event_id"
    
    elif action == "SUGGEST":
        # SUGGEST should have message and optional times
        if not payload.get("message"):
            return False, "SUGGEST action requires message"
    
    elif action == "ASK":
        # ASK should have message
        if not payload.get("message"):
            return False, "ASK action requires message"
    
    # Validate reminders if provided
    if payload.get("reminders"):
        if not isinstance(payload["reminders"], list):
            return False, "reminders must be a list"
        for offset in payload["reminders"]:
            if not isinstance(offset, int) or offset < 0:
                return False, "reminder offsets must be non-negative integers"
    
    return True, None


def validate_against_global_rules(action_data: Dict[str, Any], existing_events: List[Dict]) -> tuple[bool, Optional[str]]:
    """
    Validate action against global rules (conflicts, duplicates, etc.).
    
    Args:
        action_data: Parsed action from AI
        existing_events: List of existing events for conflict checking
        
    Returns:
        (is_valid, error_message)
    """
    action = action_data.get("action")
    payload = action_data.get("payload", {})
    
    # Rule: Movement = create new + delete old (enforced in apply_action)
    # Rule: No duplicates
    if action == "CREATE":
        start_time = payload.get("start_time")
        end_time = payload.get("end_time")
        title = payload.get("title", "").lower()
        
        if start_time and end_time:
            try:
                start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                
                # Normalize to timezone-naive UTC for comparison
                start = normalize_datetime_for_comparison(start)
                end = normalize_datetime_for_comparison(end)
                
                # Check for duplicates (same title and overlapping time)
                for event in existing_events:
                    event_start = event.get("start_time")
                    event_end = event.get("end_time")
                    event_title = event.get("title", "").lower()
                    
                    if isinstance(event_start, str):
                        event_start = datetime.fromisoformat(event_start.replace("Z", "+00:00"))
                    if isinstance(event_end, str):
                        event_end = datetime.fromisoformat(event_end.replace("Z", "+00:00"))
                    
                    # Normalize existing event times
                    event_start = normalize_datetime_for_comparison(event_start)
                    event_end = normalize_datetime_for_comparison(event_end)
                    
                    if event_title == title:
                        # Check overlap
                        if not (end <= event_start or start >= event_end):
                            return False, f"Duplicate event detected: '{event.get('title')}' overlaps with existing event"
            except (ValueError, AttributeError):
                pass  # Time parsing failed, skip conflict check
    
    # Rule: Conflict resolution
    if action == "CREATE" or (action == "UPDATE" and payload.get("start_time")):
        start_time = payload.get("start_time")
        end_time = payload.get("end_time")
        
        if start_time and end_time:
            try:
                start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                
                # Check for conflicts (overlapping events)
                # Normalize to timezone-naive UTC for comparison
                start = normalize_datetime_for_comparison(start)
                end = normalize_datetime_for_comparison(end)
                
                conflicts = []
                for event in existing_events:
                    if action == "UPDATE" and event.get("id") == payload.get("event_id"):
                        continue  # Skip the event being updated
                    
                    event_start = event.get("start_time")
                    event_end = event.get("end_time")
                    
                    if isinstance(event_start, str):
                        event_start = datetime.fromisoformat(event_start.replace("Z", "+00:00"))
                    if isinstance(event_end, str):
                        event_end = datetime.fromisoformat(event_end.replace("Z", "+00:00"))
                    
                    # Normalize existing event times
                    event_start = normalize_datetime_for_comparison(event_start)
                    event_end = normalize_datetime_for_comparison(event_end)
                    
                    # Check overlap
                    if not (end <= event_start or start >= event_end):
                        conflicts.append(event.get("title", "Untitled"))
                
                if conflicts:
                    # Return CONFLICT action instead of failing
                    return True, None  # Let the action proceed, but mark as CONFLICT
            except (ValueError, AttributeError):
                pass  # Time parsing failed, skip conflict check
    
    return True, None


async def parse_user_input(
    user_text: str,
    context_events: Optional[List[Dict]] = None,
    user_memory: Optional[Dict] = None,
    existing_events: Optional[List[Dict]] = None,
) -> AIActionResponse:
    """
    Parse user natural language input and validate against rules.
    
    Args:
        user_text: User's natural language input
        context_events: Recent events for context
        user_memory: User preferences
        existing_events: All existing events for conflict checking
        
    Returns:
        Validated AIActionResponse
    """
    # Call AI engine
    result = await ai_engine.parse_natural_language(
        user_text=user_text,
        context_events=context_events,
        user_memory=user_memory,
    )
    
    # Validate schema
    is_valid, error = validate_ai_action(result)
    if not is_valid:
        logger.warning(f"AI action validation failed: {error}")
        return AIActionResponse(
            action="ASK",
            payload=AIActionPayload(message=f"I couldn't process that request. {error}"),
            confidence=0.0,
            summary="Validation error",
        )
    
    # Validate against global rules
    existing = existing_events or []
    is_valid, error = validate_against_global_rules(result, existing)
    if not is_valid:
        logger.warning(f"Global rules validation failed: {error}")
        return AIActionResponse(
            action="CONFLICT",
            payload=AIActionPayload(message=error or "This action conflicts with existing events."),
            confidence=result.get("confidence", 0.0),
            summary=error or "Conflict detected",
        )
    
    # Check for conflicts and mark as CONFLICT if needed
    action = result.get("action")
    payload = result.get("payload", {})
    
    if action in ("CREATE", "UPDATE") and existing:
        start_time = payload.get("start_time")
        end_time = payload.get("end_time")
        
        if start_time and end_time:
            try:
                start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                
                # Normalize to timezone-naive UTC for comparison
                start = normalize_datetime_for_comparison(start)
                end = normalize_datetime_for_comparison(end)
                
                conflicts = []
                for event in existing:
                    if action == "UPDATE" and event.get("id") == payload.get("event_id"):
                        continue
                    
                    event_start = event.get("start_time")
                    event_end = event.get("end_time")
                    
                    if isinstance(event_start, str):
                        event_start = datetime.fromisoformat(event_start.replace("Z", "+00:00"))
                    if isinstance(event_end, str):
                        event_end = datetime.fromisoformat(event_end.replace("Z", "+00:00"))
                    
                    # Normalize existing event times
                    event_start = normalize_datetime_for_comparison(event_start)
                    event_end = normalize_datetime_for_comparison(event_end)
                    
                    # Check for actual overlap: events conflict if they overlap in time
                    # Two events overlap if: start < other_end AND end > other_start
                    if start < event_end and end > event_start:
                        event_title = event.get("title", "Untitled")
                        # Format times for better message
                        try:
                            event_start_str = event_start.strftime("%H:%M") if isinstance(event_start, datetime) else str(event_start)
                            event_end_str = event_end.strftime("%H:%M") if isinstance(event_end, datetime) else str(event_end)
                            conflicts.append(f"'{event_title}' ({event_start_str}-{event_end_str})")
                        except Exception:
                            conflicts.append(f"'{event_title}'")
                
                if conflicts:
                    result["action"] = "CONFLICT"
                    conflicts_str = ", ".join(conflicts)
                    result["payload"]["message"] = (
                        f"You have a conflict: {conflicts_str}. "
                        f"Would you like to reschedule?"
                    )
            except (ValueError, AttributeError) as e:
                logger.warning(f"Error in conflict detection: {e}")
                pass
    
    # Build response
    # Convert datetime strings to datetime objects if needed
    payload_for_schema = payload.copy()
    if payload.get("start_time") and isinstance(payload["start_time"], str):
        try:
            payload_for_schema["start_time"] = datetime.fromisoformat(payload["start_time"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass  # Keep as string, let Pydantic handle it
    if payload.get("end_time") and isinstance(payload["end_time"], str):
        try:
            payload_for_schema["end_time"] = datetime.fromisoformat(payload["end_time"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass  # Keep as string, let Pydantic handle it
    
    try:
        payload_obj = AIActionPayload(**payload_for_schema)
    except Exception as e:
        logger.error(f"Error creating AIActionPayload: {e}, payload: {payload_for_schema}", exc_info=True)
        # Return a safe fallback
        return AIActionResponse(
            action="ASK",
            payload=AIActionPayload(message="I couldn't parse that request. Please try rephrasing."),
            confidence=0.0,
            summary="Parsing error",
        )
    
    # Ensure summary is always a string (not None)
    summary = result.get("summary")
    if not summary or not isinstance(summary, str):
        # Fallback to message or default
        summary = payload.get("message") or "Action parsed"
    
    return AIActionResponse(
        action=result.get("action", "ASK"),
        payload=payload_obj,
        confidence=result.get("confidence", 0.0),
        summary=summary,
    )

