# Backend API Documentation

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

## API Endpoints

### Base URL
- Local: `http://localhost:8000`
- Production: Your deployed URL

### Authentication

Most endpoints require the `X-Telegram-User-Id` header:

```
X-Telegram-User-Id: 123456789
```

### Users

#### Create/Get Session
```http
POST /api/v1/users/session
Content-Type: application/json

{
  "init_data": "telegram_webapp_init_data_string"
}
```

#### Get Current User
```http
GET /api/v1/users/me
X-Telegram-User-Id: 123456789
```

#### Update User
```http
PUT /api/v1/users/me
X-Telegram-User-Id: 123456789
Content-Type: application/json

{
  "timezone": "America/New_York",
  "metadata": {}
}
```

### Events

#### List Events
```http
GET /api/v1/events?start_date=2024-01-01T00:00:00Z&end_date=2024-01-31T23:59:59Z&page=1&page_size=50
X-Telegram-User-Id: 123456789
```

#### Get Event
```http
GET /api/v1/events/{event_id}
X-Telegram-User-Id: 123456789
```

#### Create Event
```http
POST /api/v1/events
X-Telegram-User-Id: 123456789
Content-Type: application/json

{
  "title": "Team Meeting",
  "description": "Weekly sync",
  "start_time": "2024-01-15T10:00:00Z",
  "end_time": "2024-01-15T11:00:00Z",
  "timezone": "UTC",
  "location": "Conference Room A",
  "reminder_offsets": [15, 60]
}
```

#### Update Event
```http
PUT /api/v1/events/{event_id}
X-Telegram-User-Id: 123456789
Content-Type: application/json

{
  "title": "Updated Title",
  "start_time": "2024-01-15T11:00:00Z"
}
```

#### Delete Event
```http
DELETE /api/v1/events/{event_id}
X-Telegram-User-Id: 123456789
```

### AI

#### Parse Natural Language
```http
POST /api/v1/ai/parse
X-Telegram-User-Id: 123456789
Content-Type: application/json

{
  "text": "Move dentist appointment to tomorrow at 5pm",
  "context_events": [],
  "user_memory": {}
}
```

Response:
```json
{
  "action": "MOVE",
  "payload": {
    "event_id": "existing-event-id",
    "start_time": "2024-01-16T17:00:00Z",
    "end_time": "2024-01-16T18:00:00Z",
    "message": "I'll move your dentist appointment to tomorrow at 5pm"
  },
  "confidence": 0.9,
  "summary": "Move dentist appointment to tomorrow at 5pm"
}
```

#### Apply AI Action
```http
POST /api/v1/events/apply_action
X-Telegram-User-Id: 123456789
Content-Type: application/json

{
  "action": "MOVE",
  "payload": {
    "event_id": "existing-event-id",
    "start_time": "2024-01-16T17:00:00Z",
    "end_time": "2024-01-16T18:00:00Z"
  },
  "original_text": "Move dentist to tomorrow at 5pm"
}
```

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Testing

```bash
# Run all tests
pytest app/tests/ -v

# Run with coverage
pytest app/tests/ -v --cov=app --cov-report=html

# Run specific test
pytest app/tests/test_events.py::test_create_event -v
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuration
│   ├── api/
│   │   └── v1/
│   │       ├── users.py     # User endpoints
│   │       ├── events.py    # Event endpoints
│   │       └── ai.py        # AI endpoints
│   ├── models/              # SQLModel models
│   ├── schemas/             # Pydantic schemas
│   ├── db/                  # Database session
│   ├── ai/                  # AI engine & parsing
│   ├── telebot/             # Telegram bot client
│   ├── workers/             # Background jobs
│   └── tests/               # Tests
├── alembic/                 # Migrations
├── requirements.txt
├── Dockerfile
└── pytest.ini
```

