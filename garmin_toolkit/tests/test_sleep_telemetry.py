"""Unit tests for Sleep Telemetry extraction in garmin_training_toolkit_sdk."""

import unittest
from unittest.mock import MagicMock

from garmin_training_toolkit_sdk.extractors.biometrics import get_sleep_data
from garmin_training_toolkit_sdk.protocol.biometrics import SleepData


class TestSleepTelemetry(unittest.TestCase):
    """Test suite for Garmin Sleep telemetry extraction."""

    def setUp(self) -> None:
        self.client = MagicMock()

    def test_extract_sleep_with_advanced_telemetry(self) -> None:
        """Test extraction of restless moments, body battery change, and 5-min HRV."""
        mock_payload = {
            "dailySleepDTO": {
                "id": 98765,
                "calendarDate": "2026-09-22",
                "sleepTimeSeconds": 27000,
                "deepSleepSeconds": 5000,
                "lightSleepSeconds": 15000,
                "remSleepSeconds": 5000,
                "awakeSleepSeconds": 2000,
                "sleepStartTimestampGMT": 1790123456000,
                "sleepEndTimestampGMT": 1790150456000,
                "sleepScores": {"overall": {"value": 82}},
                "restlessMomentsCount": 17,
            },
            "bodyBatteryChange": 48,
            "avgOvernightHrv": 64.5,
            "hrvReadings": [
                {"readingTimeGmt": "2026-09-22T01:00:00.0", "hrvValue": 62.0},
                {"readingTimeGmt": "2026-09-22T01:05:00.0", "hrvValue": 66.0},
            ],
        }
        self.client.get_sleep_data.return_value = mock_payload

        results = get_sleep_data(self.client, "2026-09-22", "2026-09-22")

        self.assertEqual(len(results), 1)
        record = results[0]
        self.assertIsInstance(record, SleepData)
        self.assertEqual(record.date, "2026-09-22")
        self.assertEqual(record.duration_sec, 27000)
        self.assertEqual(record.quality, 82)
        self.assertEqual(record.restless_moments, 17)
        self.assertEqual(record.body_battery_change, 48)
        self.assertEqual(record.avg_overnight_hrv, 64.5)
        self.assertEqual(len(record.hrv_readings), 2)
        self.assertEqual(record.hrv_readings[0][1], 62.0)
        self.assertEqual(record.hrv_readings[1][1], 66.0)

    def test_extract_sleep_legacy_payload_graceful_defaults(self) -> None:
        """Test extraction when optional telemetry fields are omitted."""
        mock_payload = {
            "dailySleepDTO": {
                "calendarDate": "2026-09-21",
                "sleepTimeSeconds": 25000,
                "sleepScores": {"overall": {"value": 75}},
            }
        }
        self.client.get_sleep_data.return_value = mock_payload

        results = get_sleep_data(self.client, "2026-09-21", "2026-09-21")
        self.assertEqual(len(results), 1)
        record = results[0]
        self.assertIsNone(record.restless_moments)
        self.assertIsNone(record.body_battery_change)
        self.assertIsNone(record.avg_overnight_hrv)
        self.assertEqual(record.hrv_readings, [])


if __name__ == "__main__":
    unittest.main()
