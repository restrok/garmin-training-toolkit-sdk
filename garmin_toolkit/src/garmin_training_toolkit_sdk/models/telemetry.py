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
    stride_length_mm: Optional[float] = None
    vertical_oscillation_cm: Optional[float] = None
    ground_contact_time_ms: Optional[float] = None
    temperature_c: Optional[float] = None
    run_walk_index: Optional[float] = None

class ActivityTelemetry(BaseModel):
    activity_id: int
    metric_count: int
    ticks: List[ActivityTelemetryPoint]
