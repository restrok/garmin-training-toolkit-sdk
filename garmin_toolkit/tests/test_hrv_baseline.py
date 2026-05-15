
import pytest
from garmin_training_toolkit_sdk.testing.mock import MockGarminClient
from garmin_training_toolkit_sdk.extractors.biometrics import get_hrv_data

def test_get_hrv_data_with_baseline():
    client = MockGarminClient()
    # Mock data is already set in the MockGarminClient
    
    start_date = "2024-05-10"
    end_date = "2024-05-10"
    
    results = get_hrv_data(client, start_date, end_date)
    
    assert len(results) == 1
    hrv = results[0]
    assert hrv.date == "2024-05-10"
    assert hrv.avg_hrv == 65.0
    assert hrv.max_hrv == 80.0
    assert hrv.status == "BALANCED"
    assert hrv.baseline_low == 60.0
    assert hrv.baseline_high == 75.0

def test_get_hrv_data_fallback_list():
    client = MockGarminClient()
    
    # Override the mock to return a list (fallback case)
    def mock_get_hrv_list(date):
        return [
            {
                "calendarDate": date,
                "lastNightAvg": 60.0,
                "lastNight5MinHigh": 75.0,
                "status": "UNBALANCED",
                "baseline": {
                    "balancedLow": 65.0,
                    "balancedUpper": 80.0
                }
            }
        ]
    client.get_hrv_data = mock_get_hrv_list
    
    start_date = "2024-05-10"
    end_date = "2024-05-10"
    
    results = get_hrv_data(client, start_date, end_date)
    
    assert len(results) == 1
    hrv = results[0]
    assert hrv.status == "UNBALANCED"
    assert hrv.baseline_low == 65.0
    assert hrv.baseline_high == 80.0

def test_get_hrv_data_missing_fields():
    client = MockGarminClient()
    
    # Mock data missing the new fields
    def mock_get_hrv_old(date):
        return {
            "hrvSummary": {
                "calendarDate": date,
                "lastNightAvg": 65.0,
                "lastNight5MinHigh": 80.0
            }
        }
    client.get_hrv_data = mock_get_hrv_old
    
    start_date = "2024-05-10"
    results = get_hrv_data(client, start_date, start_date)
    
    assert len(results) == 1
    hrv = results[0]
    assert hrv.status is None
    assert hrv.baseline_low is None
    assert hrv.baseline_high is None
