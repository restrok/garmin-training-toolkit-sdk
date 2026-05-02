from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
from pydantic import BaseModel
from ..protocol.activities import Activity
from ..protocol.telemetry import ActivityTelemetry
from ..protocol.workouts import WorkoutPlan
from ..protocol.biometrics import HRVData, SleepData
from ..protocol.user import UserProfile

class SuccessReport(BaseModel):
    success: bool
    message: str
    uploaded_ids: List[str] = []

class BaseBiometricProvider(ABC):
    """
    Abstract Base Class for biometric and activity data providers (Garmin, Suunto, Whoop, etc.)
    """
    
    @abstractmethod
    def get_activities(self, start_date: date, end_date: date) -> List[Activity]:
        """Fetch list of activities within a date range."""
        pass

    @abstractmethod
    def get_telemetry(self, activity_id: str) -> ActivityTelemetry:
        """Fetch high-resolution telemetry for a specific activity."""
        pass

    @abstractmethod
    def upload_training_plan(self, plan: WorkoutPlan) -> SuccessReport:
        """Upload a full training plan (multiple workouts) to the provider."""
        pass

    @abstractmethod
    def get_calendar_range(self, start_date: date, end_date: date) -> List[dict]:
        """Fetch all scheduled items within a date range."""
        pass

    @abstractmethod
    def unschedule_workout(self, calendar_item_id: str) -> bool:
        """Remove a workout from the calendar."""
        pass

    @abstractmethod
    def delete_workout_template(self, workout_id: str) -> bool:
        """Permanently delete a workout definition."""
        pass

    @abstractmethod
    def get_sleep_history(self, start_date: date, end_date: date) -> List[SleepData]:
        """Fetch sleep data for a date range."""
        pass

    @abstractmethod
    def get_hrv_history(self, start_date: date, end_date: date) -> List[HRVData]:
        """Fetch HRV data for a date range."""
        pass

    @abstractmethod
    def get_user_profile(self) -> Optional[UserProfile]:
        """Fetch the user's biometric profile."""
        pass
