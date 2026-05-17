"""Pydantic models for biometric data."""

from typing import Optional

from pydantic import BaseModel


class HRVData(BaseModel):
    """Heart Rate Variability data.

    Attributes:
        date: The calendar date (YYYY-MM-DD).
        last_night_avg: Average HRV during the last night.
        min_hrv: Minimum HRV during the last night.
        max_hrv: Maximum HRV during the last night.
        status: HRV status (e.g., "BALANCED").
        baseline_low: Lower bound of the user's HRV baseline.
        baseline_high: Upper bound of the user's HRV baseline.
    """

    date: str
    last_night_avg: Optional[float] = None
    min_hrv: Optional[float] = None
    max_hrv: Optional[float] = None
    status: Optional[str] = None
    baseline_low: Optional[float] = None
    baseline_high: Optional[float] = None


class SleepData(BaseModel):
    """Sleep session data.

    Attributes:
        date: The calendar date (YYYY-MM-DD).
        start: Start timestamp (GMT).
        end: End timestamp (GMT).
        duration_sec: Total sleep duration in seconds.
        deep_sec: Deep sleep duration in seconds.
        light_sec: Light sleep duration in seconds.
        rem_sec: REM sleep duration in seconds.
        awake_sec: Awake duration in seconds.
        quality: Sleep quality score (0-100).
    """

    date: str
    start: Optional[int] = None
    end: Optional[int] = None
    duration_sec: Optional[int] = None
    deep_sec: Optional[int] = None
    light_sec: Optional[int] = None
    rem_sec: Optional[int] = None
    awake_sec: Optional[int] = None
    quality: Optional[int] = None


class ReadinessData(BaseModel):
    """Training readiness data.

    Attributes:
        date: The calendar date (YYYY-MM-DD).
        value: Readiness score (0-100).
        status: Readiness status string.
    """

    date: str
    value: Optional[int] = None
    status: Optional[str] = None


class BodyBatteryData(BaseModel):
    """Body battery data.

    Attributes:
        date: The calendar date (YYYY-MM-DD).
        charged: Amount charged during the day.
        drained: Amount drained during the day.
        highest: Highest level reached.
        lowest: Lowest level reached.
        values_count: Number of raw data points collected.
    """

    date: str
    charged: Optional[int] = None
    drained: Optional[int] = None
    highest: Optional[int] = None
    lowest: Optional[int] = None
    values_count: int = 0


class StressData(BaseModel):
    """Daily stress data.

    Attributes:
        date: The calendar date (YYYY-MM-DD).
        max_stress_level: Maximum stress level during the day.
        avg_stress_level: Average stress level during the day.
        stress_duration_sec: Total stress duration in seconds.
        rest_duration_sec: Total rest duration in seconds.
        activity_duration_sec: Total activity duration in seconds.
        low_stress_duration_sec: Low stress duration in seconds.
        medium_stress_duration_sec: Medium stress duration in seconds.
        high_stress_duration_sec: High stress duration in seconds.
    """

    date: str
    max_stress_level: Optional[int] = None
    avg_stress_level: Optional[int] = None
    stress_duration_sec: Optional[int] = None
    rest_duration_sec: Optional[int] = None
    activity_duration_sec: Optional[int] = None
    low_stress_duration_sec: Optional[int] = None
    medium_stress_duration_sec: Optional[int] = None
    high_stress_duration_sec: Optional[int] = None


class TrainingStatusData(BaseModel):
    """Training status and load data.

    Attributes:
        date: The calendar date (YYYY-MM-DD).
        status: Current training status (e.g., "PRODUCTIVE").
        acute_load: Acute training load.
        chronic_load: Chronic training load.
        load_focus: Training load focus description.
        vo2max: Current VO2 Max value.
    """

    date: str
    status: Optional[str] = None
    acute_load: Optional[float] = None
    chronic_load: Optional[float] = None
    load_focus: Optional[str] = None
    vo2max: Optional[float] = None
