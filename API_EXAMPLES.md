# API Examples

## cURL Examples

### 1. Create User Session

```bash
curl -X POST "http://localhost:8000/api/v1/users/session" \
  -H "Content-Type: application/json" \
  -d '{
    "init_data": "user=%7B%22id%22%3A123456789%2C%22first_name%22%3A%22John%22%7D&auth_date=1234567890&hash=..."
  }'
```

### 2. List Events

```bash
curl -X GET "http://localhost:8000/api/v1/events?start_date=2024-01-01T00:00:00Z&end_date=2024-01-31T23:59:59Z" \
  -H "X-Telegram-User-Id: 123456789"
```

### 3. Create Event

```bash
curl -X POST "http://localhost:8000/api/v1/events" \
  -H "Content-Type: application/json" \
  -H "X-Telegram-User-Id: 123456789" \
  -d '{
    "title": "Team Meeting",
    "description": "Weekly sync with the team",
    "start_time": "2024-01-15T10:00:00Z",
    "end_time": "2024-01-15T11:00:00Z",
    "timezone": "UTC",
    "location": "Conference Room A",
    "reminder_offsets": [15, 60]
  }'
```

### 4. Update Event

```bash
curl -X PUT "http://localhost:8000/api/v1/events/event-id-here" \
  -H "Content-Type: application/json" \
  -H "X-Telegram-User-Id: 123456789" \
  -d '{
    "title": "Updated Team Meeting",
    "start_time": "2024-01-15T11:00:00Z",
    "end_time": "2024-01-15T12:00:00Z"
  }'
```

### 5. Delete Event

```bash
curl -X DELETE "http://localhost:8000/api/v1/events/event-id-here" \
  -H "X-Telegram-User-Id: 123456789"
```

### 6. Parse Natural Language

```bash
curl -X POST "http://localhost:8000/api/v1/ai/parse" \
  -H "Content-Type: application/json" \
  -H "X-Telegram-User-Id: 123456789" \
  -d '{
    "text": "Move dentist appointment to tomorrow at 5pm"
  }'
```

### 7. Apply AI Action

```bash
curl -X POST "http://localhost:8000/api/v1/events/apply_action" \
  -H "Content-Type: application/json" \
  -H "X-Telegram-User-Id: 123456789" \
  -d '{
    "action": "MOVE",
    "payload": {
      "event_id": "existing-event-id",
      "start_time": "2024-01-16T17:00:00Z",
      "end_time": "2024-01-16T18:00:00Z"
    },
    "original_text": "Move dentist to tomorrow at 5pm"
  }'
```

## Python Examples

```python
import httpx

BASE_URL = "http://localhost:8000"
USER_ID = 123456789

# List events
response = httpx.get(
    f"{BASE_URL}/api/v1/events",
    headers={"X-Telegram-User-Id": str(USER_ID)},
    params={
        "start_date": "2024-01-01T00:00:00Z",
        "end_date": "2024-01-31T23:59:59Z"
    }
)
events = response.json()

# Create event
response = httpx.post(
    f"{BASE_URL}/api/v1/events",
    headers={
        "X-Telegram-User-Id": str(USER_ID),
        "Content-Type": "application/json"
    },
    json={
        "title": "Team Meeting",
        "start_time": "2024-01-15T10:00:00Z",
        "end_time": "2024-01-15T11:00:00Z",
        "reminder_offsets": [15, 60]
    }
)
event = response.json()

# Parse AI
response = httpx.post(
    f"{BASE_URL}/api/v1/ai/parse",
    headers={
        "X-Telegram-User-Id": str(USER_ID),
        "Content-Type": "application/json"
    },
    json={
        "text": "Schedule a meeting tomorrow at 3pm"
    }
)
ai_response = response.json()
```

## JavaScript/TypeScript Examples

```typescript
const BASE_URL = "http://localhost:8000";
const USER_ID = 123456789;

// List events
const eventsResponse = await fetch(
  `${BASE_URL}/api/v1/events?start_date=2024-01-01T00:00:00Z&end_date=2024-01-31T23:59:59Z`,
  {
    headers: {
      "X-Telegram-User-Id": USER_ID.toString(),
    },
  }
);
const events = await eventsResponse.json();

// Create event
const createResponse = await fetch(`${BASE_URL}/api/v1/events`, {
  method: "POST",
  headers: {
    "X-Telegram-User-Id": USER_ID.toString(),
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    title: "Team Meeting",
    start_time: "2024-01-15T10:00:00Z",
    end_time: "2024-01-15T11:00:00Z",
    reminder_offsets: [15, 60],
  }),
});
const event = await createResponse.json();

// Parse AI
const aiResponse = await fetch(`${BASE_URL}/api/v1/ai/parse`, {
  method: "POST",
  headers: {
    "X-Telegram-User-Id": USER_ID.toString(),
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    text: "Schedule a meeting tomorrow at 3pm",
  }),
});
const aiResult = await aiResponse.json();
```

## Postman Collection

Import this JSON into Postman:

```json
{
  "info": {
    "name": "Telegram Calendar API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Create Session",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"init_data\": \"your_telegram_init_data\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/api/v1/users/session",
          "host": ["{{base_url}}"],
          "path": ["api", "v1", "users", "session"]
        }
      }
    },
    {
      "name": "List Events",
      "request": {
        "method": "GET",
        "header": [{"key": "X-Telegram-User-Id", "value": "{{user_id}}"}],
        "url": {
          "raw": "{{base_url}}/api/v1/events",
          "host": ["{{base_url}}"],
          "path": ["api", "v1", "events"]
        }
      }
    }
  ],
  "variable": [
    {"key": "base_url", "value": "http://localhost:8000"},
    {"key": "user_id", "value": "123456789"}
  ]
}
```

