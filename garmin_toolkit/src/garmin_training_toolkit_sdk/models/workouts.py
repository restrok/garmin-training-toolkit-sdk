from pydantic import BaseModel, Field, RootModel, field_validator
from typing import List, Optional, Union, Any, Dict

class WorkoutTarget(BaseModel):
    workoutTargetTypeId: int
    workoutTargetTypeKey: str
    displayOrder: int
    targetValueOne: Optional[float] = None
    targetValueTwo: Optional[float] = None
    zone: Optional[Dict[str, Any]] = None

class WorkoutStep(BaseModel):
    type: str # warmup, run, recovery, cooldown, interval
    duration: float
    target: Optional[Union[WorkoutTarget, str, dict]] = None

    @classmethod
    def from_list(cls, data: list):
        """Convert from legacy list format [type, duration, target]"""
        step_type = data[0]
        duration = data[1]
        target = data[2] if len(data) > 2 else None
        return cls(type=step_type, duration=duration, target=target)

class WorkoutTemplate(BaseModel):
    name: str
    description: Optional[str] = ""
    duration: float
    date: str # YYYY-MM-DD
    steps: List[Union[WorkoutStep, list]]

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
    root: List[WorkoutTemplate]
