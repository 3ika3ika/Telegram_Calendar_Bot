"""Background scheduler for reminders and periodic tasks."""
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.db.session import AsyncSessionLocal
from app.models.event import Event
from app.models.reminder import Reminder
from app.telebot.client import telegram_bot

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def send_due_reminders():
    """Check and send reminders that are due."""
    async with AsyncSessionLocal() as session:
        try:
            now = datetime.utcnow()
            
            # Find events with reminders that need to be sent
            # We check events starting in the next 24 hours
            future_time = now + timedelta(days=1)
            
            result = await session.execute(
                select(Event, Reminder).join(
                    Reminder, Event.id == Reminder.event_id
                ).where(
                    and_(
                        Event.start_time >= now,
                        Event.start_time <= future_time,
                        Reminder.sent_at.is_(None),  # Not sent yet
                    )
                )
            )
            
            reminders_to_send = result.all()
            
            for event, reminder in reminders_to_send:
                # Calculate when reminder should be sent
                reminder_time = event.start_time - timedelta(minutes=reminder.offset_minutes)
                
                # Check if it's time to send (within 1 minute window)
                if now >= reminder_time - timedelta(minutes=1) and now <= reminder_time + timedelta(minutes=1):
                    # Send reminder
                    event_time_str = event.start_time.strftime("%Y-%m-%d %H:%M UTC")
                    success = await telegram_bot.send_reminder(
                        user_id=event.user_id,
                        event_title=event.title,
                        event_time=event_time_str,
                        offset_minutes=reminder.offset_minutes,
                    )
                    
                    if success:
                        reminder.sent_at = now
                        logger.info(f"Sent reminder for event {event.id} to user {event.user_id}")
                    else:
                        logger.warning(f"Failed to send reminder for event {event.id}")
            
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error sending reminders: {e}", exc_info=True)
            await session.rollback()


def start_scheduler():
    """Start the background scheduler."""
    if scheduler.running:
        logger.warning("Scheduler is already running")
        return
    
    # Schedule reminder checking every minute
    scheduler.add_job(
        send_due_reminders,
        trigger=CronTrigger(second=0),  # Every minute at :00 seconds
        id="send_reminders",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("Background scheduler started")


def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")

