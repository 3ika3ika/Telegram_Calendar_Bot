"""User schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TelegramInitData(BaseModel):
    """Telegram WebApp initData for verification."""
    init_data: str  # Raw initData string from Telegram.WebApp.initData


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    telegram_user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    timezone: str
    subscription_plan: str
    subscription_expires_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user settings."""
    timezone: Optional[str] = None
    metadata: Optional[dict] = None

