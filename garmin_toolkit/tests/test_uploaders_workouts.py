import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from garmin_training_toolkit_sdk.uploaders.workouts import load_workouts

def test_load_workouts_missing_file(mocker):
    """Verify load_workouts returns an empty list if workouts.json is missing."""
    # Patch the WORKOUTS_FILE object itself
    with patch("garmin_training_toolkit_sdk.uploaders.workouts.WORKOUTS_FILE") as mock_file:
        mock_file.exists.return_value = False
        
        # Call the function
        workouts = load_workouts()
        
        # Verify
        assert workouts == []
        mock_file.exists.assert_called_once()

def test_load_workouts_success(mocker):
    """Verify load_workouts returns a list of dictionaries if file is valid."""
    # Create mock data that WorkoutPlan can parse
    mock_data = {
        "root": [
            {
                "name": "Test Workout",
                "date": "2026-05-01",
                "steps": [{"type": "run", "duration": 600}]
            }
        ]
    }
    
    # Patch dependencies
    with patch("garmin_training_toolkit_sdk.uploaders.workouts.WORKOUTS_FILE") as mock_file, \
         patch("garmin_training_toolkit_sdk.uploaders.workouts.validate_workouts_file") as mock_validate, \
         patch("builtins.open", mocker.mock_open(read_data='{}')), \
         patch("json.load") as mock_json_load, \
         patch("garmin_training_toolkit_sdk.uploaders.workouts.WorkoutPlan") as mock_plan_cls:
        
        mock_file.exists.return_value = True
        mock_validate.return_value = (True, [])
        mock_json_load.return_value = mock_data
        
        # Mock the plan instance and its root items
        mock_workout = MagicMock()
        mock_workout.model_dump.return_value = mock_data["root"][0]
        
        mock_plan = MagicMock()
        mock_plan.root = [mock_workout]
        mock_plan_cls.return_value = mock_plan
        
        # Call the function
        workouts = load_workouts()
        
        # Verify
        assert len(workouts) == 1
        assert workouts[0]["name"] == "Test Workout"
