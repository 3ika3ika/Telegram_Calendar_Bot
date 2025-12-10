"""Telegram bot client for sending messages."""
import logging
import httpx
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class TelegramBotClient:
    """Client for sending messages via Telegram Bot API."""
    
    def __init__(self):
        """Initialize Telegram bot client."""
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}"
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: Optional[str] = "HTML",
    ) -> bool:
        """
        Send a message to a Telegram user.
        
        Args:
            chat_id: Telegram user ID
            text: Message text
            parse_mode: HTML or Markdown
            
        Returns:
            True if successful, False otherwise
        """
        if not self.token:
            logger.warning("TELEGRAM_BOT_TOKEN not set - cannot send messages")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": parse_mode,
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    async def send_reminder(
        self,
        user_id: int,
        event_title: str,
        event_time: str,
        offset_minutes: int,
    ) -> bool:
        """
        Send a reminder message for an event.
        
        Args:
            user_id: Telegram user ID
            event_title: Event title
            event_time: Event time (formatted string)
            offset_minutes: Minutes before event (e.g., 15, 60, 1440)
            
        Returns:
            True if successful
        """
        # Format offset
        if offset_minutes < 60:
            offset_str = f"{offset_minutes} minutes"
        elif offset_minutes < 1440:
            offset_str = f"{offset_minutes // 60} hours"
        else:
            offset_str = f"{offset_minutes // 1440} days"
        
        text = (
            f"📅 <b>Reminder: {event_title}</b>\n\n"
            f"⏰ {event_time}\n"
            f"⏳ {offset_str} until event"
        )
        
        return await self.send_message(user_id, text)
    
    async def edit_message_text(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        parse_mode: Optional[str] = "HTML",
        reply_markup: Optional[dict] = None,
    ) -> bool:
        """
        Edit a message's text and/or reply markup.
        
        Args:
            chat_id: Telegram chat ID
            message_id: Message ID to edit
            text: New message text
            parse_mode: HTML or Markdown
            reply_markup: Inline keyboard markup (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.token:
            logger.warning("TELEGRAM_BOT_TOKEN not set - cannot edit messages")
            return False
        
        try:
            payload = {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "parse_mode": parse_mode,
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/editMessageText",
                    json=payload,
                    timeout=10.0,
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to edit Telegram message: {e}")
            return False
    
    async def edit_message_reply_markup(
        self,
        chat_id: int,
        message_id: int,
        reply_markup: Optional[dict] = None,
    ) -> bool:
        """
        Edit only the reply markup (inline keyboard) of a message.
        
        Args:
            chat_id: Telegram chat ID
            message_id: Message ID to edit
            reply_markup: New inline keyboard markup (None to remove)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.token:
            logger.warning("TELEGRAM_BOT_TOKEN not set - cannot edit messages")
            return False
        
        try:
            payload = {
                "chat_id": chat_id,
                "message_id": message_id,
            }
            if reply_markup is not None:
                payload["reply_markup"] = reply_markup
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/editMessageReplyMarkup",
                    json=payload,
                    timeout=10.0,
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to edit Telegram message reply markup: {e}")
            return False
    
    async def delete_message(
        self,
        chat_id: int,
        message_id: int,
    ) -> bool:
        """
        Delete a message.
        
        Args:
            chat_id: Telegram chat ID
            message_id: Message ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.token:
            logger.warning("TELEGRAM_BOT_TOKEN not set - cannot delete messages")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/deleteMessage",
                    json={
                        "chat_id": chat_id,
                        "message_id": message_id,
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to delete Telegram message: {e}")
            return False


# Global instance
telegram_bot = TelegramBotClient()

