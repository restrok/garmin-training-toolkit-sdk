from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class HRVData(BaseModel):
    date: str
    avg_hrv: Optional[float] = None
    min_hrv: Optional[float] = None
    max_hrv: Optional[float] = None

class SleepData(BaseModel):
    date: str
    start: Optional[str] = None
    end: Optional[str] = None
    duration_sec: Optional[float] = None
    deep_sec: Optional[float] = None
    light_sec: Optional[float] = None
    rem_sec: Optional[float] = None
    awake_sec: Optional[float] = None
    quality: Optional[str] = None

class ReadinessData(BaseModel):
    date: str
    value: Optional[int] = None
    status: Optional[str] = None
