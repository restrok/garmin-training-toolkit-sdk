from typing import List, Optional
from pydantic import BaseModel

class ActivityTelemetryPoint(BaseModel):
    timestamp_ms: int
    lat: Optional[float] = None
    lng: Optional[float] = None
    elevation_m: Optional[float] = None
    speed_mps: Optional[float] = None
    hr_bpm: Optional[float] = None
    cadence_spm: Optional[float] = None
    power_w: Optional[float] = None
    fractional_cadence: Optional[float] = None
    gap_mps: Optional[float] = None  # Grade Adjusted Pace

class ActivityTelemetry(BaseModel):
    activity_id: int
    metric_count: int
    ticks: List[ActivityTelemetryPoint]
