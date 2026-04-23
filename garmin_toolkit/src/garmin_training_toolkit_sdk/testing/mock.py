from typing import Any, List
from datetime import datetime

class MockGarminClient:
    """
    A mock client for Garmin Connect API testing.
    Exposes the same interface as garminconnect.Garmin.
    """
    def __init__(self):
        self.workouts = []
        self.scheduled_workouts = []
        self.deleted_workout_ids = []
        self.unscheduled_item_ids = []
        self.uploaded_workouts = []

    def get_workouts(self) -> List[dict]:
        return self.workouts

    def delete_workout(self, workout_id: str):
        self.deleted_workout_ids.append(str(workout_id))
        self.workouts = [w for w in self.workouts if str(w.get("workoutId")) != str(workout_id)]
        self.scheduled_workouts = [w for w in self.scheduled_workouts if str(w.get("workoutId")) != str(workout_id)]
        return True

    def upload_workout(self, workout_dict: dict) -> dict:
        workout_id = str(len(self.uploaded_workouts) + 1000)
        workout_data = {
            "workoutId": workout_id,
            "workoutName": workout_dict.get("workoutName", "Mock Workout"),
        }
        self.uploaded_workouts.append(workout_dict)
        self.workouts.append(workout_data)
        return workout_data

    def upload_running_workout(self, workout: Any) -> dict:
        # Legacy/Compatibility
        return self.upload_workout(getattr(workout, "__dict__", {}))

    def schedule_workout(self, workout_id: str, workout_date: str):
        # Check if workout exists
        workout = next((w for w in self.workouts if str(w.get("workoutId")) == str(workout_id)), None)
        item = {
            "workoutId": str(workout_id),
            "calendarItemId": str(len(self.scheduled_workouts) + 5000),
            "date": workout_date,
            "itemType": "workout",
            "title": workout.get("workoutName") if workout else "Scheduled Workout"
        }
        self.scheduled_workouts.append(item)
        return True

    def unschedule_workout(self, calendar_item_id: str):
        self.unscheduled_item_ids.append(str(calendar_item_id))
        self.scheduled_workouts = [w for w in self.scheduled_workouts if str(w.get("calendarItemId")) != str(calendar_item_id)]
        return True

    def get_scheduled_workouts(self, year: int, month: int) -> dict:
        items = []
        for w in self.scheduled_workouts:
            dt = datetime.strptime(w["date"], "%Y-%m-%d")
            if dt.year == year and dt.month == month:
                items.append(w)
        return {"calendarItems": items}
