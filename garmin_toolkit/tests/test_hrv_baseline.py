"""Tests for HRV baseline and status extraction."""

from typing import Any, Dict, List

from garmin_training_toolkit_sdk.extractors.biometrics import get_hrv_data
from garmin_training_toolkit_sdk.testing.mock import MockGarminClient


def test_get_hrv_data_with_baseline() -> None:
    """Tests get_hrv_data correctly extracts baseline and status fields."""
    client = MockGarminClient()

    start_date = "2024-05-10"
    end_date = "2024-05-10"

    results = get_hrv_data(client, start_date, end_date)

    assert len(results) == 1
    hrv = results[0]
    assert hrv.date == "2024-05-10"
    assert hrv.last_night_avg == 65.0
    assert hrv.max_hrv == 80.0
    assert hrv.status == "BALANCED"
    assert hrv.baseline_low == 60.0
    assert hrv.baseline_high == 75.0


def test_get_hrv_data_fallback_list() -> None:
    """Tests get_hrv_data correctly handles fallback to list response."""
    client = MockGarminClient()

    def mock_get_hrv_list(date: str) -> List[Dict[str, Any]]:
        """Mock implementation returning a list of HRV data."""
        return [
            {
                "calendarDate": date,
                "lastNightAvg": 60.0,
                "lastNight5MinHigh": 75.0,
                "status": "UNBALANCED",
                "baseline": {"balancedLow": 65.0, "balancedUpper": 80.0},
            }
        ]

    client.get_hrv_data = mock_get_hrv_list  # type: ignore

    start_date = "2024-05-10"
    end_date = "2024-05-10"

    results = get_hrv_data(client, start_date, end_date)

    assert len(results) == 1
    hrv = results[0]
    assert hrv.status == "UNBALANCED"
    assert hrv.baseline_low == 65.0
    assert hrv.baseline_high == 80.0


def test_get_hrv_data_missing_fields() -> None:
    """Tests get_hrv_data correctly handles missing baseline fields."""
    client = MockGarminClient()

    def mock_get_hrv_old(date: str) -> Dict[str, Any]:
        """Mock implementation missing new HRV fields."""
        return {
            "hrvSummary": {
                "calendarDate": date,
                "lastNightAvg": 65.0,
                "lastNight5MinHigh": 80.0,
            }
        }

    client.get_hrv_data = mock_get_hrv_old  # type: ignore

    start_date = "2024-05-10"
    results = get_hrv_data(client, start_date, start_date)

    assert len(results) == 1
    hrv = results[0]
    assert hrv.status is None
    assert hrv.baseline_low is None
    assert hrv.baseline_high is None
