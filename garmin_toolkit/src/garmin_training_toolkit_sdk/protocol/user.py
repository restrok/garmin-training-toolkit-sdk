from typing import Optional
from pydantic import BaseModel
from datetime import date

class UserProfile(BaseModel):
    display_name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    max_hr: Optional[int] = None
    resting_hr: Optional[int] = None

class BodyComposition(BaseModel):
    date: date
    weight_kg: Optional[float] = None
    bmi: Optional[float] = None
    fat_percentage: Optional[float] = None
    muscle_mass_kg: Optional[float] = None
    water_percentage: Optional[float] = None
