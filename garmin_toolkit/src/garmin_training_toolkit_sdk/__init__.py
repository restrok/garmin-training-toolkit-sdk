from .utils import get_authenticated_client
from .protocol.activities import Activity, ActivitySplit
from .protocol.biometrics import HRVData, SleepData, ReadinessData, BodyBatteryData, StressData, TrainingStatusData
from .protocol.telemetry import ActivityTelemetry, ActivityTelemetryPoint
from .extractors.activities import get_activities, get_activity_splits, get_activity_telemetry
from .extractors.biometrics import get_hrv_data, get_sleep_data, get_readiness_data, get_body_battery, get_stress_data, get_training_status

# The uploaders and weather modules are available but not imported at root level to keep the namespace clean
# import garmin_training_toolkit_sdk.uploaders.workouts
# import garmin_training_toolkit_sdk.weather

__all__ = [
    "get_authenticated_client",
    "Activity",
    "ActivitySplit",
    "HRVData",
    "SleepData",
    "ReadinessData",
    "BodyBatteryData",
    "StressData",
    "TrainingStatusData",
    "ActivityTelemetry",
    "ActivityTelemetryPoint",
    "get_activities",
    "get_activity_splits",
    "get_activity_telemetry",
    "get_hrv_data",
    "get_sleep_data",
    "get_readiness_data",
    "get_body_battery",
    "get_stress_data",
    "get_training_status"
]
