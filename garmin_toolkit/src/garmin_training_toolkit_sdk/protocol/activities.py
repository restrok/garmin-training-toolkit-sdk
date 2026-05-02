from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class ActivitySplit(BaseModel):
    index: int
    type: Optional[str] = None
    distance_m: Optional[float] = None
    duration_sec: Optional[float] = None
    moving_duration_sec: Optional[float] = None
    avg_hr: Optional[float] = None
    max_hr: Optional[float] = None
    avg_pace_mps: Optional[float] = None
    avg_cadence: Optional[float] = None
    calories: Optional[float] = None
    # Swimming Specific
    strokes: Optional[float] = None
    avg_swolf: Optional[float] = None
    # Cycling Specific
    avg_power: Optional[float] = None
    max_power: Optional[float] = None

class Activity(BaseModel):
    id: int
    name: str
    type: str
    date: datetime
    duration_sec: Optional[float] = None
    distance_m: Optional[float] = None
    avg_hr: Optional[float] = None
    max_hr: Optional[float] = None
    avg_pace: Optional[float] = None
    calories: Optional[float] = None
    elevation_gain: Optional[float] = None
    vo2max: Optional[float] = None
    # Swimming Specific
    pool_length_m: Optional[float] = None
    total_strokes: Optional[float] = None
    avg_swolf: Optional[float] = None
    # Cycling Specific
    avg_power: Optional[float] = None
    max_power: Optional[float] = None
    normalized_power: Optional[float] = None
    avg_cadence: Optional[float] = None
    max_cadence: Optional[float] = None
    splits: Optional[List[ActivitySplit]] = Field(default_factory=list)
