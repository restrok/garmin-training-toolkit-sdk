import logging
import random
import time
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..extractors.activities import get_activities as fetch_activities
from ..extractors.activities import get_activity_telemetry
from ..extractors.biometrics import get_hrv_data as fetch_hrv
from ..extractors.biometrics import get_sleep_data as fetch_sleep
from ..extractors.biometrics import get_user_profile as fetch_user_profile
from ..protocol.activities import Activity
from ..protocol.biometrics import HRVData, SleepData
from ..protocol.telemetry import ActivityTelemetry
from ..protocol.user import UserProfile
from ..protocol.workouts import WorkoutPlan, WorkoutTemplateSummary
from ..uploaders.calendar import schedule_workout
from ..uploaders.workouts import create_workout
from ..uploaders.workouts import delete_workout as perform_delete
from ..utils import (
    REQUEST_DELAY_MAX,
    REQUEST_DELAY_MIN,
    find_token_file,
    get_authenticated_client,
    refresh_if_unauthorized,
)
from .base import BaseBiometricProvider, SuccessReport

log = logging.getLogger(__name__)


class GarminProvider(BaseBiometricProvider):
    """Garmin Connect implementation of the Biometric Provider.

    Attributes:
        token_path: Path to the Garmin tokens file.
        client: Authenticated Garmin API client.
    """

    def __init__(self, token_path: Optional[Path] = None) -> None:
        """Initialize the GarminProvider.

        Args:
            token_path: Optional path to the Garmin tokens file.

        Raises:
            Exception: If Garmin tokens are not found.
        """
        self.token_path = token_path or find_token_file()
        if not self.token_path:
            raise Exception("Garmin tokens not found. Please authenticate first.")
        self.client = get_authenticated_client(self.token_path)

    @refresh_if_unauthorized
    def get_activities(self, start_date: date, end_date: date) -> List[Activity]:
        """Fetch activities from Garmin Connect.

        Args:
            start_date: Start date for the activity search.
            end_date: End date for the activity search.

        Returns:
            A list of Activity objects.
        """
        # Current extractor: get_activities(client, start_date_str, end_date_str, limit=20)
        all_raw = fetch_activities(
            self.client, start_date.isoformat(), end_date.isoformat(), limit=50
        )
        filtered = []
        for act in all_raw:
            if start_date <= act.date.date() <= end_date:
                filtered.append(act)
        return filtered

    @refresh_if_unauthorized
    def get_telemetry(self, activity_id: str) -> ActivityTelemetry:
        """Fetch telemetry for a Garmin activity.

        Args:
            activity_id: The ID of the activity.

        Returns:
            An ActivityTelemetry object.
        """
        return get_activity_telemetry(self.client, int(activity_id))

    @refresh_if_unauthorized
    def upload_training_plan(self, plan: WorkoutPlan) -> SuccessReport:
        """Upload and schedule workouts from a plan.

        Args:
            plan: The WorkoutPlan to upload.

        Returns:
            A SuccessReport indicating the result of the upload.
        """
        uploaded_ids = []
        try:
            for workout_template in plan.root:
                log.info("Uploading workout: %s", workout_template.name)
                workout_payload = create_workout(workout_template.model_dump())

                result = self.client.upload_workout(workout_payload)
                workout_id = result.get("workoutId")
                uploaded_ids.append(str(workout_id))

                time.sleep(
                    REQUEST_DELAY_MIN
                    + random.uniform(0, REQUEST_DELAY_MAX - REQUEST_DELAY_MIN)
                )

                log.info(
                    "Scheduling %s for %s", workout_template.name, workout_template.date
                )
                schedule_workout(self.client, workout_id, workout_template.date)

                time.sleep(
                    REQUEST_DELAY_MIN
                    + random.uniform(0, REQUEST_DELAY_MAX - REQUEST_DELAY_MIN)
                )

            return SuccessReport(
                success=True,
                message="Successfully uploaded %d workouts" % len(uploaded_ids),
                uploaded_ids=uploaded_ids,
            )
        except Exception as e:
            log.error("Failed to upload training plan: %s", e)
            return SuccessReport(
                success=False, message=str(e), uploaded_ids=uploaded_ids
            )

    @refresh_if_unauthorized
    def get_scheduled_workouts(self, workout_date: Union[date, str]) -> Dict[str, Any]:
        """Fetch scheduled workouts for the month containing workout_date.

        Accepts YYYY-MM-DD string or date object.
        Standardizes positional (year, month) to a single date-based query.

        Args:
            workout_date: The date to fetch workouts for (either date object or string).

        Returns:
            A dictionary containing scheduled workouts data.
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

        log.debug("Fetching scheduled workouts for %d-%d", dt.year, dt.month)
        return self.client.get_scheduled_workouts(dt.year, dt.month)

    @refresh_if_unauthorized
    def get_workout_templates(self) -> List[WorkoutTemplateSummary]:
        """Fetch all workout templates from the library.

        Returns:
            A list of WorkoutTemplateSummary objects.

        Raises:
            Exception: If fetching templates fails.
        """
        log.info("Fetching workout templates from Garmin library...")
        try:
            raw_workouts = self.client.get_workouts()
            return [WorkoutTemplateSummary(**w) for w in raw_workouts]
        except Exception as e:
            log.error("Failed to fetch workout templates: %s", e)
            raise

    @refresh_if_unauthorized
    def get_calendar_range(
        self, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """Fetch all scheduled items between start_date and end_date (inclusive).

        Handles pagination across month boundaries internally.

        Args:
            start_date: The start date of the range.
            end_date: The end date of the range.

        Returns:
            A list of dictionary objects representing calendar items.
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
            log.debug("Fetching calendar for %d-%d", year, month)
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
                log.error("Failed to fetch calendar for %d-%d: %s", year, month, e)

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

    @refresh_if_unauthorized
    def unschedule_workout(self, calendar_item_id: str) -> bool:
        """Remove a workout from the calendar.

        Args:
            calendar_item_id: The ID of the calendar item to remove.

        Returns:
            True if successful, False otherwise.
        """
        try:
            self.client.unschedule_workout(calendar_item_id)
            return True
        except Exception as e:
            log.error("Failed to unschedule workout %s: %s", calendar_item_id, e)
            return False

    @refresh_if_unauthorized
    def delete_workout_template(self, workout_id: str) -> bool:
        """Permanently delete a workout definition.

        Args:
            workout_id: The ID of the workout to delete.

        Returns:
            True if successful, False otherwise.
        """
        return perform_delete(self.client, workout_id)

    @refresh_if_unauthorized
    def get_sleep_history(self, start_date: date, end_date: date) -> List[SleepData]:
        """Fetch sleep data for a date range.

        Args:
            start_date: Start date for the sleep history.
            end_date: End date for the sleep history.

        Returns:
            A list of SleepData objects.
        """
        return fetch_sleep(self.client, start_date.isoformat(), end_date.isoformat())

    @refresh_if_unauthorized
    def get_hrv_history(self, start_date: date, end_date: date) -> List[HRVData]:
        """Fetch HRV data for a date range.

        Args:
            start_date: Start date for the HRV history.
            end_date: End date for the HRV history.

        Returns:
            A list of HRVData objects.
        """
        return fetch_hrv(self.client, start_date.isoformat(), end_date.isoformat())

    @refresh_if_unauthorized
    def get_user_profile(self) -> Optional[UserProfile]:
        """Fetch the user's biometric profile.

        Returns:
            A UserProfile object if successful, None otherwise.
        """
        return fetch_user_profile(self.client)
