from typing import Optional
from pydantic import BaseModel

class HRVData(BaseModel):
    date: str
    avg_hrv: Optional[float] = None
    min_hrv: Optional[float] = None
    max_hrv: Optional[float] = None

class SleepData(BaseModel):
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
    date: str
    value: Optional[int] = None
    status: Optional[str] = None

class BodyBatteryData(BaseModel):
    date: str
    charged: Optional[int] = None
    drained: Optional[int] = None
    highest: Optional[int] = None
    lowest: Optional[int] = None
    values_count: int = 0

class StressData(BaseModel):
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
    date: str
    status: Optional[str] = None
    acute_load: Optional[float] = None
    chronic_load: Optional[float] = None
    load_focus: Optional[str] = None
    vo2max: Optional[float] = None
