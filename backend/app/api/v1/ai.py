"""AI parsing endpoints."""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_session
from app.models.event import Event
from app.schemas.ai import AIParseRequest, AIActionResponse
from app.ai.parse import parse_user_input

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])


def get_user_id(telegram_user_id: int = Header(..., alias="X-Telegram-User-Id")) -> int:
    """Dependency to extract telegram_user_id from header."""
    return telegram_user_id


@router.post("/parse", response_model=AIActionResponse)
async def parse_natural_language(
    request: AIParseRequest,
    user_id: int = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
):
    """
    Parse natural language input into structured action.
    
    This endpoint:
    1. Gets user's recent events for context
    2. Calls AI engine with system prompt
    3. Validates AI response against global rules
    4. Returns structured action with summary
    """
    # Get recent events for context (last 30 days)
    # Use timezone-naive UTC datetime for database comparison
    now = datetime.utcnow()
    start_date = now - timedelta(days=30)
    result = await session.execute(
        select(Event).where(
            Event.user_id == user_id,
            Event.start_time >= start_date,
        ).order_by(Event.start_time.desc()).limit(20)
    )
    recent_events = result.scalars().all()
    
    # Convert to dict for context
    context_events = [
        {
            "id": e.id,
            "title": e.title,
            "start_time": e.start_time.isoformat(),
            "end_time": e.end_time.isoformat(),
            "description": e.description,
        }
        for e in recent_events
    ]
    
    # Get all events for conflict checking (next 90 days)
    end_date = now + timedelta(days=90)
    result_all = await session.execute(
        select(Event).where(
            Event.user_id == user_id,
            Event.start_time >= now,
            Event.start_time <= end_date,
        )
    )
    all_future_events = result_all.scalars().all()
    
    existing_events = [
        {
            "id": e.id,
            "title": e.title,
            "start_time": e.start_time.isoformat(),
            "end_time": e.end_time.isoformat(),
        }
        for e in all_future_events
    ]
    
    # Parse user input
    try:
        response = await parse_user_input(
            user_text=request.text,
            context_events=context_events,
            user_memory=request.user_memory,
            existing_events=existing_events,
        )
        return response
    except ValueError as e:
        # Common case: OpenAI client not initialized (missing OPENAI_API_KEY)
        msg = str(e)
        if "OpenAI client not initialized" in msg:
            raise HTTPException(status_code=503, detail="AI is not configured (missing OPENAI_API_KEY).")
        logger.error(f"Error parsing natural language: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to parse input: {msg}")
    except Exception as e:
        logger.error(f"Error parsing natural language: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to parse input")

