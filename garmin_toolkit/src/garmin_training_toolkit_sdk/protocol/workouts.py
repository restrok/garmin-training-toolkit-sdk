"""Workout-related Pydantic models and helper functions."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Sequence, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator,
    model_validator,
)


class WorkoutTemplateSummary(BaseModel):
    """Summary of a workout template in the library.

    Attributes:
        workout_id: The unique ID of the workout.
        workout_name: The name of the workout.
        sport_type: The sport type key (e.g., 'running').
        created_date: When the workout was created.
        updated_date: When the workout was last updated.
        owner_id: The ID of the workout owner.
        description: A text description of the workout.
    """

    model_config = ConfigDict(populate_by_name=True)

    workout_id: str = Field(alias="workoutId")
    workout_name: str = Field(alias="workoutName")
    sport_type: Optional[str] = Field(alias="sportTypeKey", default=None)
    created_date: Optional[datetime] = Field(alias="createdDate", default=None)
    updated_date: Optional[datetime] = Field(alias="updatedDate", default=None)
    owner_id: Optional[str] = Field(alias="ownerId", default=None)
    description: Optional[str] = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def flatten_sport_type(cls, data: Any) -> Any:
        """Flatten nested sportType data from Garmin API.

        Args:
            data: The raw dictionary from the API.

        Returns:
            The flattened dictionary.
        """
        if isinstance(data, dict):
            # Garmin often nests sportType or uses sportTypeKey directly
            sport_data = data.get("sportType")
            if isinstance(sport_data, dict) and "sportTypeKey" in sport_data:
                data["sportTypeKey"] = sport_data["sportTypeKey"]

            # Ensure IDs are strings as requested
            if "workoutId" in data and data["workoutId"] is not None:
                data["workoutId"] = str(data["workoutId"])
            if "ownerId" in data and data["ownerId"] is not None:
                data["ownerId"] = str(data["ownerId"])
        return data


class HeartRateTarget(BaseModel):
    """Target based on heart rate BPM.

    Attributes:
        target_type: Literal discriminator 'heart.rate'.
        min_bpm: Minimum heart rate in beats per minute.
        max_bpm: Maximum heart rate in beats per minute.
    """

    target_type: Literal["heart.rate"] = "heart.rate"
    min_bpm: int
    max_bpm: int


class PaceTarget(BaseModel):
    """Target based on pace (seconds per kilometer).

    Attributes:
        target_type: Literal discriminator 'pace'.
        min_pace_seconds: Minimum pace in seconds per kilometer.
        max_pace_seconds: Maximum pace in seconds per kilometer.
    """

    target_type: Literal["pace"] = "pace"
    min_pace_seconds: int
    max_pace_seconds: int


class PowerTarget(BaseModel):
    """Target based on power (Watts).

    Attributes:
        target_type: Literal discriminator 'power'.
        min_watts: Minimum power in Watts.
        max_watts: Maximum power in Watts.
    """

    target_type: Literal["power"] = "power"
    min_watts: int
    max_watts: int


class WorkoutTarget(BaseModel):
    """Intensity target for a workout step (e.g., a heart rate zone or pace).

    Attributes:
        target_type: The type of intensity target.
        min_target: The lower boundary of the target.
        max_target: The upper boundary of the target.
        target_type_id: Internal Garmin field for target type ID.
        display_order: Internal Garmin field for display order.
        zone: Internal Garmin field for zone information.
    """

    model_config = ConfigDict(populate_by_name=True)

    target_type: Literal["heart.rate.zone", "speed.zone", "power.zone", "no.target"] = (
        Field(
            default="no.target",
            alias="workoutTargetTypeKey",
            description="The type of intensity target.",
        )
    )
    min_target: Optional[float] = Field(
        default=None,
        alias="targetValueOne",
        description="The lower boundary of the target.",
    )
    max_target: Optional[float] = Field(
        default=None,
        alias="targetValueTwo",
        description="The upper boundary of the target.",
    )

    # Internal Garmin fields
    target_type_id: Optional[int] = Field(default=None, alias="workoutTargetTypeId")
    display_order: Optional[int] = Field(default=None, alias="displayOrder")
    zone: Optional[Dict[str, Any]] = None

    @field_validator("min_target", "max_target")
    @classmethod
    def validate_hr_range(cls, v: Optional[float], info: Any) -> Optional[float]:
        """Validate heart rate range is realistic.

        Args:
            v: The value to validate.
            info: Pydantic validation info.

        Returns:
            The validated value.

        Raises:
            ValueError: If the value is outside the realistic range.
        """
        if info.data.get("target_type") == "heart.rate.zone" and v is not None:
            if not (40 <= v <= 220):
                raise ValueError(
                    "Heart rate value %.1f is outside realistic range (40-220 BPM)" % v
                )
        return v


class WorkoutStep(BaseModel):
    """A single instruction in a workout (e.g., Warmup for 10 minutes or 400m).

    Attributes:
        type: The category of the step.
        duration: Legacy duration in minutes.
        duration_mins: Duration of the step in minutes.
        distance_m: Distance of the step in meters.
        target: Intensity target.
    """

    type: Literal["warmup", "run", "recovery", "cooldown", "interval"] = Field(
        description="The category of the step."
    )
    duration: Optional[float] = Field(
        default=None,
        description="Legacy: Duration in minutes.",
    )
    duration_mins: Optional[float] = Field(
        default=None,
        description="Duration of the step in minutes.",
    )
    distance_m: Optional[float] = Field(
        default=None,
        description="Distance of the step in meters.",
    )
    target: Optional[
        Union[
            HeartRateTarget, PaceTarget, PowerTarget, WorkoutTarget, str, Dict[str, Any]
        ]
    ] = Field(
        default=None,
        description="Intensity target.",
    )

    @model_validator(mode="after")
    def validate_durations(self) -> "WorkoutStep":
        """Ensure exactly one duration type is provided.

        Returns:
            The validated WorkoutStep.

        Raises:
            ValueError: If no duration or multiple durations are provided.
        """
        durations = [self.duration, self.duration_mins, self.distance_m]
        provided = [d for d in durations if d is not None]
        if not provided:
            raise ValueError(
                "Exactly one of 'duration_mins', 'distance_m' (or legacy 'duration') "
                "must be provided."
            )
        if len(provided) > 1:
            raise ValueError(
                "Only one of 'duration_mins', 'distance_m' (or legacy 'duration') "
                "can be provided."
            )
        return self

    @classmethod
    def from_list(cls, data: list) -> "WorkoutStep":
        """Convert from legacy list format [type, duration, target].

        Args:
            data: A list of [type, duration, target].

        Returns:
            A new WorkoutStep instance.
        """
        step_type = data[0]
        duration = data[1]
        target = data[2] if len(data) > 2 else None
        return cls(type=step_type, duration=duration, target=target)


class RepeatGroup(BaseModel):
    """A group of steps to be repeated multiple times.

    Attributes:
        type: Literal discriminator 'repeat'.
        iterations: Number of times to repeat the steps.
        steps: The list of steps to repeat.
    """

    type: Literal["repeat"] = "repeat"
    iterations: int = Field(gt=0, description="Number of times to repeat the steps.")
    steps: List[WorkoutStep] = Field(description="The steps to repeat.")


class WorkoutTemplate(BaseModel):
    """Full definition of a workout to be uploaded to Garmin.

    Attributes:
        name: The name of the workout.
        description: Detailed description of the workout.
        duration: Total estimated duration in minutes.
        date: The scheduled date in YYYY-MM-DD format.
        steps: List of workout steps or repeat groups.
    """

    name: str = Field(description="The name of the workout.")
    description: Optional[str] = Field(
        default="", description="Optional detailed description."
    )
    duration: float = Field(description="Total estimated duration in minutes.")
    date: str = Field(description="The scheduled date in YYYY-MM-DD format.")
    steps: Sequence[Union[WorkoutStep, RepeatGroup, list]] = Field(
        description="List of workout steps or repeat groups."
    )

    @field_validator("steps")
    @classmethod
    def validate_steps(
        cls, v: Sequence[Union[WorkoutStep, RepeatGroup, list]]
    ) -> List[Union[WorkoutStep, RepeatGroup]]:
        """Pre-process steps to ensure they are correct Pydantic models.

        Args:
            v: The sequence of steps.

        Returns:
            A list of validated steps.
        """
        processed_steps = []
        for step in v:
            if isinstance(step, list):
                processed_steps.append(WorkoutStep.from_list(step))
            elif isinstance(step, dict) and step.get("type") == "repeat":
                processed_steps.append(RepeatGroup(**step))
            else:
                processed_steps.append(step)  # type: ignore
        return processed_steps


class WorkoutPlan(RootModel):
    """A plan containing multiple workout templates."""

    root: Sequence[WorkoutTemplate]


# Helper / Quick Start Functions


def create_simple_hr_workout(
    name: str,
    date_str: str,
    bpm_min: int,
    bpm_max: int,
    duration_mins: int,
    warmup_mins: int = 10,
    cooldown_mins: int = 10,
) -> WorkoutTemplate:
    """Quickly create a standard Heart Rate based workout.

    Args:
        name: Name of the workout.
        date_str: Scheduled date (YYYY-MM-DD).
        bpm_min: Minimum BPM target.
        bpm_max: Maximum BPM target.
        duration_mins: Main set duration in minutes.
        warmup_mins: Warmup duration in minutes.
        cooldown_mins: Cooldown duration in minutes.

    Returns:
        A WorkoutTemplate object.
    """
    steps = []
    if warmup_mins > 0:
        steps.append(WorkoutStep(type="warmup", duration_mins=float(warmup_mins)))

    steps.append(
        WorkoutStep(
            type="run",
            duration_mins=float(duration_mins),
            target=HeartRateTarget(min_bpm=bpm_min, max_bpm=bpm_max),
        )
    )

    if cooldown_mins > 0:
        steps.append(WorkoutStep(type="cooldown", duration_mins=float(cooldown_mins)))

    return WorkoutTemplate(
        name=name,
        date=date_str,
        duration=float(warmup_mins + duration_mins + cooldown_mins),
        steps=steps,
    )


def create_simple_pace_workout(
    name: str,
    date_str: str,
    pace: str,
    duration_mins: int,
    warmup_mins: int = 10,
    cooldown_mins: int = 10,
) -> WorkoutTemplate:
    """Quickly create a standard Pace based workout.

    Args:
        name: Name of the workout.
        date_str: Scheduled date (YYYY-MM-DD).
        pace: Pace target (e.g. "5:00 min/km").
        duration_mins: Main set duration in minutes.
        warmup_mins: Warmup duration in minutes.
        cooldown_mins: Cooldown duration in minutes.

    Returns:
        A WorkoutTemplate object.
    """
    steps = []
    if warmup_mins > 0:
        steps.append(WorkoutStep(type="warmup", duration_mins=float(warmup_mins)))

    steps.append(
        WorkoutStep(type="run", duration_mins=float(duration_mins), target=pace)
    )

    if cooldown_mins > 0:
        steps.append(WorkoutStep(type="cooldown", duration_mins=float(cooldown_mins)))

    return WorkoutTemplate(
        name=name,
        date=date_str,
        duration=float(warmup_mins + duration_mins + cooldown_mins),
        steps=steps,
    )
