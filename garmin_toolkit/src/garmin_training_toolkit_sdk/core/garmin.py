import logging
import random
import time
from datetime import date
from typing import List, Optional
from pathlib import Path

from .base import BaseBiometricProvider, SuccessReport
from ..protocol.activities import Activity
from ..protocol.telemetry import ActivityTelemetry
from ..protocol.workouts import WorkoutPlan
from ..extractors.activities import get_activities as fetch_activities, get_activity_telemetry
from ..uploaders.workouts import create_workout, schedule_workout
from ..utils import find_token_file, get_authenticated_client, REQUEST_DELAY_MIN, REQUEST_DELAY_MAX

log = logging.getLogger(__name__)

class GarminProvider(BaseBiometricProvider):
    """
    Garmin Connect implementation of the Biometric Provider.
    """
    
    def __init__(self, token_path: Optional[Path] = None):
        self.token_path = token_path or find_token_file()
        if not self.token_path:
            raise Exception("Garmin tokens not found. Please authenticate first.")
        self.client = get_authenticated_client(self.token_path)

    def get_activities(self, start_date: date, end_date: date) -> List[Activity]:
        """Fetch activities from Garmin Connect."""
        # Current extractor: get_activities(client, start_date_str, end_date_str, limit=20)
        all_raw = fetch_activities(self.client, start_date.isoformat(), end_date.isoformat(), limit=50)
        filtered = []
        for act in all_raw:
            if start_date <= act.date.date() <= end_date:
                filtered.append(act)
        return filtered

    def get_telemetry(self, activity_id: str) -> ActivityTelemetry:
        """Fetch telemetry for a Garmin activity."""
        return get_activity_telemetry(self.client, int(activity_id))

    def upload_training_plan(self, plan: WorkoutPlan) -> SuccessReport:
        """Upload and schedule workouts from a plan."""
        uploaded_ids = []
        try:
            for workout_template in plan.root:
                log.info(f"Uploading workout: {workout_template.name}")
                workout_payload = create_workout(workout_template.model_dump())
                
                result = self.client.upload_workout(workout_payload)
                workout_id = result.get("workoutId")
                uploaded_ids.append(str(workout_id))
                
                time.sleep(REQUEST_DELAY_MIN + random.uniform(0, REQUEST_DELAY_MAX - REQUEST_DELAY_MIN))
                
                log.info(f"Scheduling {workout_template.name} for {workout_template.date}")
                schedule_workout(self.client, workout_id, workout_template.date)
                
                time.sleep(REQUEST_DELAY_MIN + random.uniform(0, REQUEST_DELAY_MAX - REQUEST_DELAY_MIN))
            
            return SuccessReport(
                success=True,
                message=f"Successfully uploaded {len(uploaded_ids)} workouts",
                uploaded_ids=uploaded_ids
            )
        except Exception as e:
            log.error(f"Failed to upload training plan: {e}")
            return SuccessReport(success=False, message=str(e), uploaded_ids=uploaded_ids)
