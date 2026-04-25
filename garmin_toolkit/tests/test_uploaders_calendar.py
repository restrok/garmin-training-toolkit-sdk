import pytest
from datetime import date
from garmin_training_toolkit_sdk.testing.mock import MockGarminClient
from garmin_training_toolkit_sdk.uploaders.calendar import clear_calendar_range

def test_clear_calendar_range_with_id_fallback():
    """Verify clear_calendar_range returns the correct count and handles id fallback."""
    client = MockGarminClient()
    
    # Add scheduled items (some with calendarItemId, some with id only)
    # MockGarminClient uses 'calendarItemId' when scheduling.
    
    client.scheduled_workouts = [
        {"calendarItemId": "123", "title": "Item 1", "date": "2026-05-15", "itemType": "workout"},
        {"id": "456", "title": "Item 2", "date": "2026-05-16", "itemType": "workout"}, # id fallback
        {"calendarItemId": "789", "title": "ATP Item", "date": "2026-05-17", "itemType": "workout", "atpPlanId": "atp1"}, # ATP should skip
    ]
    
    # Call clear_calendar_range
    cleared_count = clear_calendar_range(client, "2026-05-01", "2026-05-31")
    
    # Verify:
    # Item 1: cleared (calendarItemId exists)
    # Item 2: cleared (id fallback exists)
    # Item 3: skipped (atpPlanId exists)
    
    assert cleared_count == 2
    assert "123" in client.unscheduled_item_ids
    assert "456" in client.unscheduled_item_ids
    assert "789" not in client.unscheduled_item_ids

def test_clear_calendar_range_empty():
    """Verify it returns 0 if no items found."""
    client = MockGarminClient()
    cleared_count = clear_calendar_range(client, "2026-05-01", "2026-05-31")
    assert cleared_count == 0
