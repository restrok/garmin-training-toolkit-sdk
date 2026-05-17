"""Tests for HRV fallback mechanism."""

import unittest
from unittest.mock import MagicMock

from garmin_training_toolkit_sdk.extractors.biometrics import get_hrv_data
from garmin_training_toolkit_sdk.protocol.biometrics import HRVData


class TestHRVFallback(unittest.TestCase):
    """Test suite for HRV fallback logic."""

    def setUp(self) -> None:
        """Set up mock Garmin client."""
        self.client = MagicMock()

    def test_hrv_fallback_on_404(self) -> None:
        """Test that HRV extraction falls back to sleep data on 404 error."""
        # 1. Setup HRV endpoint to fail with 404
        self.client.get_hrv_data.side_effect = Exception("404 Not Found")

        # 2. Setup Sleep endpoint to return HRV data
        self.client.get_sleep_data.return_value = {
            "avgOvernightHrv": 42.0,
            "hrvStatus": "BALANCED",
            "calendarDate": "2026-05-16",
        }

        # 3. Call get_hrv_data
        results = get_hrv_data(self.client, "2026-05-16", "2026-05-16")

        # 4. Assertions
        self.assertEqual(len(results), 1)
        hrv = results[0]
        self.assertIsInstance(hrv, HRVData)
        self.assertEqual(hrv.date, "2026-05-16")
        self.assertEqual(hrv.last_night_avg, 42.0)
        self.assertEqual(hrv.status, "BALANCED")

        # Ensure both endpoints were called
        self.client.get_hrv_data.assert_called_with("2026-05-16")
        self.client.get_sleep_data.assert_called_with(cdate="2026-05-16")

    def test_hrv_no_fallback_on_other_error(self) -> None:
        """Test that HRV extraction does not fallback on non-404/400 errors."""
        # 1. Setup HRV endpoint to fail with 500
        self.client.get_hrv_data.side_effect = Exception("500 Internal Server Error")

        # 2. Call get_hrv_data
        results = get_hrv_data(self.client, "2026-05-16", "2026-05-16")

        # 3. Assertions
        self.assertEqual(len(results), 0)
        self.client.get_sleep_data.assert_not_called()

    def test_hrv_fallback_graceful_degradation(self) -> None:
        """Test that HRV extraction handles cases where both endpoints fail."""
        # 1. Setup HRV endpoint to fail with 404
        self.client.get_hrv_data.side_effect = Exception("404 Not Found")

        # 2. Setup Sleep endpoint to return no HRV data
        self.client.get_sleep_data.return_value = {
            "calendarDate": "2026-05-16",
            "dailySleepDTO": {"sleepTimeSeconds": 28800},
        }

        # 3. Call get_hrv_data
        results = get_hrv_data(self.client, "2026-05-16", "2026-05-16")

        # 4. Assertions
        self.assertEqual(len(results), 0)
        self.client.get_sleep_data.assert_called_once()


if __name__ == "__main__":
    unittest.main()
