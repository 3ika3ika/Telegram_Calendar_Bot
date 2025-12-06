"""Tests for event endpoints."""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.main import app
from app.models.event import Event
from app.models.user import User

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def test_db():
    """Create test database."""
    async with engine.begin() as conn:
        from app.models import *
        from sqlmodel import SQLModel
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
async def test_user(test_db):
    """Create test user."""
    async with TestSessionLocal() as session:
        user = User(
            telegram_user_id=123456789,
            username="testuser",
            first_name="Test",
            timezone="UTC",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.mark.asyncio
async def test_create_event(test_user):
    """Test creating an event."""
    client = TestClient(app)
    
    response = client.post(
        "/api/v1/events",
        json={
            "title": "Test Event",
            "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "end_time": (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat(),
        },
        headers={"X-Telegram-User-Id": str(test_user.telegram_user_id)},
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Event"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_events(test_user):
    """Test listing events."""
    client = TestClient(app)
    
    # Create an event first
    response = client.post(
        "/api/v1/events",
        json={
            "title": "Test Event",
            "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "end_time": (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat(),
        },
        headers={"X-Telegram-User-Id": str(test_user.telegram_user_id)},
    )
    assert response.status_code == 201
    
    # List events
    response = client.get(
        "/api/v1/events",
        headers={"X-Telegram-User-Id": str(test_user.telegram_user_id)},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert len(data["events"]) >= 1

