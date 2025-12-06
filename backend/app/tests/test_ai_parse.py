"""Tests for AI parsing and validation."""
import pytest
from datetime import datetime, timedelta
from app.ai.parse import validate_ai_action, validate_against_global_rules
from app.schemas.ai import AIActionPayload


def test_validate_ai_action_create():
    """Test validation of CREATE action."""
    action_data = {
        "action": "CREATE",
        "payload": {
            "title": "Test Event",
            "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "end_time": (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat(),
        }
    }
    is_valid, error = validate_ai_action(action_data)
    assert is_valid, f"Validation failed: {error}"


def test_validate_ai_action_create_missing_fields():
    """Test validation fails when required fields are missing."""
    action_data = {
        "action": "CREATE",
        "payload": {
            "title": "Test Event",
            # Missing start_time and end_time
        }
    }
    is_valid, error = validate_ai_action(action_data)
    assert not is_valid
    assert "start_time" in error or "end_time" in error


def test_validate_ai_action_update():
    """Test validation of UPDATE action."""
    action_data = {
        "action": "UPDATE",
        "payload": {
            "event_id": "test-id",
            "title": "Updated Title",
        }
    }
    is_valid, error = validate_ai_action(action_data)
    assert is_valid, f"Validation failed: {error}"


def test_validate_ai_action_delete():
    """Test validation of DELETE action."""
    action_data = {
        "action": "DELETE",
        "payload": {
            "event_id": "test-id",
        }
    }
    is_valid, error = validate_ai_action(action_data)
    assert is_valid, f"Validation failed: {error}"


def test_validate_ai_action_invalid_action():
    """Test validation fails for invalid action."""
    action_data = {
        "action": "INVALID",
        "payload": {}
    }
    is_valid, error = validate_ai_action(action_data)
    assert not is_valid
    assert "Invalid action" in error


def test_validate_against_global_rules_duplicate():
    """Test duplicate detection."""
    action_data = {
        "action": "CREATE",
        "payload": {
            "title": "Test Event",
            "start_time": datetime.utcnow().isoformat(),
            "end_time": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        }
    }
    existing_events = [
        {
            "id": "existing-1",
            "title": "test event",
            "start_time": datetime.utcnow().isoformat(),
            "end_time": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        }
    ]
    is_valid, error = validate_against_global_rules(action_data, existing_events)
    assert not is_valid
    assert "Duplicate" in error or "duplicate" in error


def test_validate_against_global_rules_conflict():
    """Test conflict detection."""
    action_data = {
        "action": "CREATE",
        "payload": {
            "title": "New Event",
            "start_time": datetime.utcnow().isoformat(),
            "end_time": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        }
    }
    existing_events = [
        {
            "id": "existing-1",
            "title": "Existing Event",
            "start_time": (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
            "end_time": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
        }
    ]
    is_valid, error = validate_against_global_rules(action_data, existing_events)
    # Conflicts should be allowed but marked
    assert is_valid

