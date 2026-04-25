from pydantic import BaseModel, RootModel, field_validator, Field, ConfigDict
from typing import Optional, Union, Any, Dict, Literal, Sequence

class WorkoutTarget(BaseModel):
    """
    Defines the intensity target for a workout step (e.g., a heart rate zone or pace).
    """
    model_config = ConfigDict(populate_by_name=True)

    target_type: Literal["heart.rate.zone", "speed.zone", "power.zone", "no.target"] = Field(
        default="no.target",
        alias="workoutTargetTypeKey",
        description="The type of intensity target. Use 'heart.rate.zone' for BPM, 'speed.zone' for pace, and 'power.zone' for watts."
    )
    min_target: Optional[float] = Field(
        default=None,
        alias="targetValueOne",
        description="The lower boundary of the target. For HR, this is BPM (e.g. 140). For Pace, this is m/s (e.g. 3.33 for 5:00/km). For Power, this is Watts."
    )
    max_target: Optional[float] = Field(
        default=None,
        alias="targetValueTwo",
        description="The upper boundary of the target. Same units as min_target."
    )
    
    # Internal Garmin fields (hidden from LLM if we use a clean view, but kept for SDK compatibility)
    target_type_id: Optional[int] = Field(default=None, alias="workoutTargetTypeId")
    display_order: Optional[int] = Field(default=None, alias="displayOrder")
    zone: Optional[Dict[str, Any]] = None

    @field_validator("min_target", "max_target")
    @classmethod
    def validate_hr_range(cls, v, info):
        if info.data.get("target_type") == "heart.rate.zone" and v is not None:
            if not (40 <= v <= 220):
                raise ValueError(f"Heart rate value {v} is outside realistic range (40-220 BPM)")
        return v

class WorkoutStep(BaseModel):
    """
    A single instruction in a workout (e.g., Warmup for 10 minutes).
    """
    type: Literal["warmup", "run", "recovery", "cooldown", "interval"] = Field(
        description="The category of the step. 'run' and 'interval' are typically the main work."
    )
    duration: float = Field(
        description="Duration of the step in minutes. Example: 10.5 for 10 minutes and 30 seconds."
    )
    target: Optional[Union[WorkoutTarget, str, dict]] = Field(
        default=None,
        description="Intensity target. Can be a structured WorkoutTarget, or a simple string like '145-155' for HR, '5:00-5:20' for Pace, or '250W' for Power."
    )

    @classmethod
    def from_list(cls, data: list):
        """Convert from legacy list format [type, duration, target]"""
        step_type = data[0]
        duration = data[1]
        target = data[2] if len(data) > 2 else None
        return cls(type=step_type, duration=duration, target=target)

class WorkoutTemplate(BaseModel):
    """
    Full definition of a workout to be uploaded to Garmin.
    """
    name: str = Field(
        description="The name of the workout as it will appear on the Garmin device. Max 30 chars recommended."
    )
    description: Optional[str] = Field(
        default="",
        description="Optional detailed description of the workout."
    )
    duration: float = Field(
        description="Total estimated duration in minutes."
    )
    date: str = Field(
        description="The scheduled date in YYYY-MM-DD format."
    )
    steps: Sequence[Union[WorkoutStep, list]] = Field(
        description="List of workout steps to perform in sequence."
    )

    @field_validator("steps")
    @classmethod
    def validate_steps(cls, v):
        processed_steps = []
        for step in v:
            if isinstance(step, list):
                processed_steps.append(WorkoutStep.from_list(step))
            else:
                processed_steps.append(step)
        return processed_steps

class WorkoutPlan(RootModel):
    root: Sequence[WorkoutTemplate]

# Helper / Quick Start Functions

def create_simple_hr_workout(name: str, date: str, bpm_min: int, bpm_max: int, duration_mins: int, warmup_mins: int = 10, cooldown_mins: int = 10) -> WorkoutTemplate:
    """
    Quickly create a standard Heart Rate based workout.
    """
    steps = []
    if warmup_mins > 0:
        steps.append(WorkoutStep(type="warmup", duration=warmup_mins))
    
    steps.append(WorkoutStep(
        type="run", 
        duration=duration_mins,
        target=WorkoutTarget(
            workoutTargetTypeKey="heart.rate.zone",
            targetValueOne=float(bpm_min),
            targetValueTwo=float(bpm_max)
        )
    ))

    if cooldown_mins > 0:
        steps.append(WorkoutStep(type="cooldown", duration=cooldown_mins))

    return WorkoutTemplate(
        name=name,
        date=date,
        duration=warmup_mins + duration_mins + cooldown_mins,
        steps=steps
    )

def create_simple_pace_workout(name: str, date: str, pace: str, duration_mins: int, warmup_mins: int = 10, cooldown_mins: int = 10) -> WorkoutTemplate:
    """
    Quickly create a standard Pace based workout.
    pace: e.g. "5:00" or "5:00 min/km"
    """
    steps = []
    if warmup_mins > 0:
        steps.append(WorkoutStep(type="warmup", duration=warmup_mins))
    
    steps.append(WorkoutStep(
        type="run", 
        duration=duration_mins,
        target=pace
    ))

    if cooldown_mins > 0:
        steps.append(WorkoutStep(type="cooldown", duration=cooldown_mins))

    return WorkoutTemplate(
        name=name,
        date=date,
        duration=warmup_mins + duration_mins + cooldown_mins,
        steps=steps
    )
