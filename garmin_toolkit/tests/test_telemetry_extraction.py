import unittest
from unittest.mock import MagicMock
from garmin_training_toolkit_sdk.extractors.activities import get_activity_telemetry
from garmin_training_toolkit_sdk.protocol.telemetry import ActivityTelemetry

class TestTelemetryExtraction(unittest.TestCase):
    def test_get_activity_telemetry_new_metrics(self):
        # Mock client
        client = MagicMock()
        
        # Mock data from Garmin activity-details
        mock_details = {
            "metricDescriptors": [
                {"key": "directTimestamp", "metricsIndex": 0},
                {"key": "directBodyBattery", "metricsIndex": 1},
                {"key": "directVerticalSpeed", "metricsIndex": 2},
                {"key": "directVerticalRatio", "metricsIndex": 3},
                {"key": "directPerformanceCondition", "metricsIndex": 4}
            ],
            "activityDetailMetrics": [
                {
                    "metrics": [1600000000000, 85.0, 0.5, 7.2, 5.0]
                },
                {
                    "metrics": [1600000001000, 84.0, 0.6, 7.1, 4.0]
                }
            ]
        }
        client.get_activity_details.return_value = mock_details
        
        telemetry = get_activity_telemetry(client, 12345678)
        
        self.assertIsInstance(telemetry, ActivityTelemetry)
        self.assertEqual(telemetry.activity_id, 12345678)
        self.assertEqual(telemetry.metric_count, 2)
        
        # Check first tick
        t1 = telemetry.ticks[0]
        self.assertEqual(t1.timestamp_ms, 1600000000000)
        self.assertEqual(t1.body_battery, 85.0)
        self.assertEqual(t1.vertical_speed, 0.5)
        self.assertEqual(t1.vertical_ratio, 7.2)
        self.assertEqual(t1.performance_condition, 5.0)
        
        # Check second tick
        t2 = telemetry.ticks[1]
        self.assertEqual(t2.timestamp_ms, 1600000001000)
        self.assertEqual(t2.body_battery, 84.0)
        self.assertEqual(t2.vertical_speed, 0.6)
        self.assertEqual(t2.vertical_ratio, 7.1)
        self.assertEqual(t2.performance_condition, 4.0)

    def test_get_activity_telemetry_missing_metrics(self):
        # Verify robustness for older devices/activities
        client = MagicMock()
        
        # Mock data without the new descriptors
        mock_details = {
            "metricDescriptors": [
                {"key": "directTimestamp", "metricsIndex": 0},
                {"key": "directHeartRate", "metricsIndex": 1}
            ],
            "activityDetailMetrics": [
                {
                    "metrics": [1600000000000, 140.0]
                }
            ]
        }
        client.get_activity_details.return_value = mock_details
        
        telemetry = get_activity_telemetry(client, 87654321)
        
        t1 = telemetry.ticks[0]
        self.assertEqual(t1.timestamp_ms, 1600000000000)
        self.assertEqual(t1.hr_bpm, 140.0)
        # New fields should be None
        self.assertIsNone(t1.body_battery)
        self.assertIsNone(t1.vertical_speed)
        self.assertIsNone(t1.vertical_ratio)
        self.assertIsNone(t1.performance_condition)

if __name__ == "__main__":
    unittest.main()
