"""User model."""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, JSON
from sqlalchemy import BigInteger


class User(SQLModel, table=True):
    """User model representing a Telegram user."""
    
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_user_id: int = Field(sa_column=Column(BigInteger, unique=True, index=True))
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    timezone: Optional[str] = Field(default="UTC")
    subscription_plan: str = Field(default="free")  # free, pro
    subscription_expires_at: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

