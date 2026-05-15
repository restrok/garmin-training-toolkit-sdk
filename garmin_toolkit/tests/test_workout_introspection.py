"""Tests for workout template introspection via the Garmin provider."""

import unittest
from datetime import datetime
from unittest.mock import patch

from garmin_training_toolkit_sdk.core.garmin import GarminProvider
from garmin_training_toolkit_sdk.testing.mock import MockGarminClient


class TestWorkoutIntrospection(unittest.TestCase):
    """Test suite for inspecting Garmin workout templates."""

    def setUp(self) -> None:
        """Sets up the test environment with a mocked Garmin client."""
        # Mock find_token_file to return a dummy path
        with patch(
            "garmin_training_toolkit_sdk.core.garmin.find_token_file"
        ) as mock_find:
            mock_find.return_value = "dummy_path"
            # Mock get_authenticated_client to return our MockGarminClient
            with patch(
                "garmin_training_toolkit_sdk.core.garmin.get_authenticated_client"
            ) as m_auth:
                self.mock_client = MockGarminClient()
                m_auth.return_value = self.mock_client
                self.provider = GarminProvider()

    def test_get_workout_templates_mapping(self) -> None:
        """Tests mapping of raw Garmin workout data to WorkoutTemplateSummary."""
        # Prepare mock raw data from Garmin
        raw_data = [
            {
                "workoutId": 12345,
                "ownerId": 67890,
                "workoutName": "Morning Run",
                "description": "Easy run in the park",
                "updatedDate": "2023-10-27T10:00:00.0",
                "createdDate": "2023-10-20T08:00:00.0",
                "sportType": {"sportTypeId": 1, "sportTypeKey": "running"},
            },
            {
                "workoutId": 54321,
                "ownerId": 98765,
                "workoutName": "Late Swim",
                "description": None,
                "updatedDate": "2023-10-27T18:00:00.0",
                "createdDate": "2023-10-25T12:00:00.0",
                "sportType": None,  # Test None sportType
            },
        ]
        self.mock_client.workouts = raw_data

        templates = self.provider.get_workout_templates()

        self.assertEqual(len(templates), 2)

        # Verify first template
        t1 = templates[0]
        self.assertEqual(t1.workout_id, "12345")  # Should be string
        self.assertEqual(t1.owner_id, "67890")  # Should be string
        self.assertEqual(t1.workout_name, "Morning Run")
        self.assertEqual(t1.sport_type, "running")
        self.assertEqual(t1.description, "Easy run in the park")
        self.assertIsInstance(t1.updated_date, datetime)

        # Verify second template
        t2 = templates[1]
        self.assertEqual(t2.workout_id, "54321")
        self.assertEqual(t2.workout_name, "Late Swim")
        self.assertIsNone(t2.sport_type)
        self.assertIsNone(t2.description)

    def test_get_workout_templates_empty(self) -> None:
        """Tests get_workout_templates when no workouts are present."""
        self.mock_client.workouts = []
        templates = self.provider.get_workout_templates()
        self.assertEqual(len(templates), 0)


if __name__ == "__main__":
    unittest.main()
