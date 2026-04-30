import logging
import random
import time
from datetime import date
from typing import List, Optional, Union
from pathlib import Path

from .base import BaseBiometricProvider, SuccessReport
from ..protocol.activities import Activity
from ..protocol.telemetry import ActivityTelemetry
from ..protocol.workouts import WorkoutPlan
from ..extractors.activities import get_activities as fetch_activities, get_activity_telemetry
from ..uploaders.workouts import create_workout
from ..uploaders.calendar import schedule_workout

from ..utils import (
    find_token_file, 
    get_authenticated_client, 
    REQUEST_DELAY_MIN, 
    REQUEST_DELAY_MAX,
    refresh_if_unauthorized
)

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

    @refresh_if_unauthorized
    def get_activities(self, start_date: date, end_date: date) -> List[Activity]:
        """Fetch activities from Garmin Connect."""
        # Current extractor: get_activities(client, start_date_str, end_date_str, limit=20)
        all_raw = fetch_activities(self.client, start_date.isoformat(), end_date.isoformat(), limit=50)
        filtered = []
        for act in all_raw:
            if start_date <= act.date.date() <= end_date:
                filtered.append(act)
        return filtered

    @refresh_if_unauthorized
    def get_telemetry(self, activity_id: str) -> ActivityTelemetry:
        """Fetch telemetry for a Garmin activity."""
        return get_activity_telemetry(self.client, int(activity_id))

    @refresh_if_unauthorized
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

    @refresh_if_unauthorized
    def get_scheduled_workouts(self, workout_date: Union[date, str]) -> dict:
        """
        Fetch scheduled workouts for the month containing workout_date.
        Accepts YYYY-MM-DD string or date object.
        Standardizes positional (year, month) to a single date-based query.
        """
        dt: date
        if isinstance(workout_date, str):
            try:
                dt = date.fromisoformat(workout_date)
            except ValueError:
                # Handle YYYY-MM-DD HH:MM:SS or similar
                dt = date.fromisoformat(workout_date.split()[0])
        else:
            dt = workout_date
        
        log.debug(f"Fetching scheduled workouts for {dt.year}-{dt.month}")
        return self.client.get_scheduled_workouts(dt.year, dt.month)

    @refresh_if_unauthorized
    def get_calendar_range(self, start_date: date, end_date: date) -> List[dict]:
        """
        Fetch all scheduled items between start_date and end_date (inclusive).
        Handles pagination across month boundaries internally.
        """
        # Fetch months covered by the range
        current = start_date.replace(day=1)
        months = []
        while current <= end_date:
            months.append((current.year, current.month))
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        all_items = []
        seen_ids = set()
        
        for year, month in months:
            log.debug(f"Fetching calendar for {year}-{month}")
            try:
                # Use a date from that month to call our standardized method
                cal_date = date(year, month, 1)
                cal = self.get_scheduled_workouts(cal_date)
                
                if cal and "calendarItems" in cal:
                    for item in cal["calendarItems"]:
                        item_id = item.get("calendarItemId") or item.get("id")
                        if item_id and item_id not in seen_ids:
                            all_items.append(item)
                            seen_ids.add(item_id)
            except Exception as e:
                log.error(f"Failed to fetch calendar for {year}-{month}: {e}")

        # Filter by date range
        filtered_items = []
        for item in all_items:
            item_date_str = item.get("date")
            if not item_date_str:
                continue
            
            try:
                item_date = date.fromisoformat(item_date_str)
                if start_date <= item_date <= end_date:
                    filtered_items.append(item)
            except ValueError:
                continue
                
        return filtered_items
