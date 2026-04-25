from abc import ABC, abstractmethod
from typing import List
from datetime import date
from pydantic import BaseModel
from ..protocol.activities import Activity
from ..protocol.telemetry import ActivityTelemetry
from ..protocol.workouts import WorkoutPlan

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
