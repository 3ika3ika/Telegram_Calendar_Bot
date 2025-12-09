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
            
            # Find all events with unsent reminders that start in the future
            # We check events starting up to 7 days in the future to catch all reminders
            future_time = now + timedelta(days=7)
            
            result = await session.execute(
                select(Event, Reminder).join(
                    Reminder, Event.id == Reminder.event_id
                ).where(
                    and_(
                        Event.start_time > now,  # Event hasn't started yet
                        Event.start_time <= future_time,
                        Reminder.sent_at.is_(None),  # Not sent yet
                    )
                )
            )
            
            reminders_to_send = result.all()
            sent_count = 0
            
            for event, reminder in reminders_to_send:
                # Calculate when reminder should be sent
                reminder_time = event.start_time - timedelta(minutes=reminder.offset_minutes)
                
                # Check if it's time to send (within 1 minute window to account for scheduler timing)
                # Also check if reminder time has passed (catch up on missed reminders within 5 minutes)
                time_diff = (now - reminder_time).total_seconds() / 60  # minutes
                if -1 <= time_diff <= 5:  # Within 1 minute before to 5 minutes after (catch up window)
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
                        sent_count += 1
                        logger.info(f"Sent reminder for event '{event.title}' (ID: {event.id}) to user {event.user_id} - {reminder.offset_minutes}min before event")
                    else:
                        logger.warning(f"Failed to send reminder for event {event.id} to user {event.user_id} - TELEGRAM_BOT_TOKEN may not be set")
            
            if sent_count > 0:
                await session.commit()
                logger.info(f"Sent {sent_count} reminder(s) successfully")
            
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

