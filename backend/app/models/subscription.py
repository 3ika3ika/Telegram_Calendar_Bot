"""Subscription plan model (reference data)."""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, JSON


class SubscriptionPlan(SQLModel, table=True):
    """Subscription plan reference data."""
    
    __tablename__ = "subscription_plans"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)  # free, pro
    max_events_per_month: Optional[int] = None  # None = unlimited
    max_ai_requests_per_day: int = Field(default=10)
    features: dict = Field(default_factory=dict, sa_column=Column(JSON))  # {"recurring": true, "teams": false}
    created_at: datetime = Field(default_factory=datetime.utcnow)

