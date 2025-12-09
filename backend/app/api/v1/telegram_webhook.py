"""Telegram bot webhook endpoint with AI action handling and voice support."""
import logging
import os
import httpx
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.db.session import get_session
from app.models.user import User
from app.models.event import Event
from app.schemas.ai import AIApplyActionRequest, AIActionPayload
from app.api.v1.ai import parse_user_input  # reuse existing AI pipeline
from app.api.v1.events import apply_ai_action  # reuse existing event applier
from app.telebot.client import telegram_bot
from app.config import settings
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/telegram", tags=["telegram"])
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None


async def get_or_create_user(telegram_user: dict, session: AsyncSession) -> User:
    """Ensure user exists in DB; create if missing."""
    telegram_user_id = telegram_user.get("id")
    if not telegram_user_id:
        raise HTTPException(status_code=400, detail="Missing user id in update")

    result = await session.execute(
        select(User).where(User.telegram_user_id == telegram_user_id)
    )
    user = result.scalar_one_or_none()
    if user:
        return user

    user = User(
        telegram_user_id=telegram_user_id,
        username=telegram_user.get("username"),
        first_name=telegram_user.get("first_name"),
        last_name=telegram_user.get("last_name"),
        language_code=telegram_user.get("language_code"),
        timezone="UTC",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def build_ai_request(message_text: str, user_id: int, session: AsyncSession) -> AIApplyActionRequest:
    """Gather context and call AI parser."""
    # Recent events for context (last 30 days)
    result_recent = await session.execute(
        select(Event)
        .where(Event.user_id == user_id)
        .order_by(Event.start_time.desc())
        .limit(20)
    )
    recent_events = result_recent.scalars().all()
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

    # Future events for conflict checking (next 90 days)
    result_future = await session.execute(
        select(Event)
        .where(Event.user_id == user_id)
        .order_by(Event.start_time)
        .limit(200)
    )
    all_future_events = result_future.scalars().all()
    existing_events = [
        {
            "id": e.id,
            "title": e.title,
            "start_time": e.start_time.isoformat(),
            "end_time": e.end_time.isoformat(),
        }
        for e in all_future_events
    ]

    ai_response = await parse_user_input(
        user_text=message_text,
        context_events=context_events,
        user_memory=None,
        existing_events=existing_events,
    )

    return AIApplyActionRequest(
        action=ai_response.action,
        payload=AIActionPayload(**ai_response.payload),
        original_text=message_text,
    )


async def transcribe_voice(file_id: str) -> Optional[str]:
    """Download and transcribe a Telegram voice note using OpenAI Whisper."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set; cannot download voice")
        return None
    if not openai_client:
        logger.warning("OPENAI_API_KEY not set; cannot transcribe voice")
        return None

    base = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"
    # Get file path
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{base}/getFile", params={"file_id": file_id}, timeout=10)
            resp.raise_for_status()
            file_path = resp.json().get("result", {}).get("file_path")
            if not file_path:
                logger.warning("No file_path returned for voice message")
                return None

            file_url = f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{file_path}"
            audio_resp = await client.get(file_url, timeout=30)
            audio_resp.raise_for_status()
            audio_bytes = audio_resp.content

        # Transcribe
        transcription = await openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=("voice.ogg", audio_bytes, "audio/ogg"),
        )
        return transcription.text
    except Exception as e:
        logger.error(f"Voice transcription failed: {e}", exc_info=True)
        return None


def format_event_summary(action: str, event):
    """Create a short summary for Telegram reply."""
    if not event:
        return "Done."
    start = getattr(event, "start_time", None)
    end = getattr(event, "end_time", None)
    start_str = start.isoformat() if start else ""
    end_str = end.isoformat() if end else ""
    return f"{action}: {getattr(event, 'title', '')}\n{start_str} — {end_str}"


@router.post("/webhook", include_in_schema=False)
async def telegram_webhook(request: Request, session: AsyncSession = Depends(get_session)):
    """
    Handle Telegram webhook updates with AI-driven event actions.
    """
    data = await request.json()
    message = data.get("message") or data.get("edited_message")
    if not message:
        return {"ok": True}  # Ignore non-message updates

    from_user = message.get("from")
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    # Handle voice
    if not text:
        voice = message.get("voice")
        if voice and voice.get("file_id"):
            text = await transcribe_voice(voice["file_id"]) or ""

    if not chat_id or not from_user or not text:
        return {"ok": True}

    # Ensure user exists
    user = await get_or_create_user(from_user, session)

    # Run AI to get action
    try:
        ai_action_req = await build_ai_request(text, user.telegram_user_id, session)
        result_event = await apply_ai_action(ai_action_req, user.telegram_user_id, session)
        summary = format_event_summary(ai_action_req.action, result_event)
        await telegram_bot.send_message(chat_id=chat_id, text=summary)
    except Exception as e:
        logger.error(f"Telegram webhook AI error: {e}", exc_info=True)
        await telegram_bot.send_message(
            chat_id=chat_id,
            text="Sorry, I couldn't process that request.",
        )

    return {"ok": True}

