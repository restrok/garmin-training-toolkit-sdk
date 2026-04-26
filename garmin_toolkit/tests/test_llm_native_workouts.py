import pytest
from garmin_training_toolkit_sdk.protocol.workouts import (
    WorkoutStep, 
    WorkoutTemplate,
    RepeatGroup,
    HeartRateTarget,
    PaceTarget,
    PowerTarget
)
from garmin_training_toolkit_sdk.uploaders.workouts import create_step_with_target, create_workout

def test_workout_step_duration_validation():
    # Valid: only duration_mins
    step = WorkoutStep(type="run", duration_mins=10)
    assert step.duration_mins == 10
    
    # Valid: only distance_m
    step = WorkoutStep(type="run", distance_m=400)
    assert step.distance_m == 400
    
    # Invalid: both
    with pytest.raises(ValueError, match="Only one of 'duration_mins', 'distance_m'"):
        WorkoutStep(type="run", duration_mins=10, distance_m=400)
        
    # Invalid: none
    with pytest.raises(ValueError, match="Exactly one of 'duration_mins', 'distance_m'"):
        WorkoutStep(type="run")

def test_explicit_target_models():
    # HR Target
    hr = HeartRateTarget(min_bpm=140, max_bpm=160)
    step = WorkoutStep(type="run", duration_mins=30, target=hr)
    payload = create_step_with_target(step.model_dump(), 1)
    assert payload["targetType"]["workoutTargetTypeKey"] == "heart.rate.zone"
    assert payload["targetType"]["targetValueOne"] == 140
    
    # Pace Target
    pace = PaceTarget(min_pace_seconds=300, max_pace_seconds=320) # 5:00 to 5:20
    step = WorkoutStep(type="run", duration_mins=30, target=pace)
    payload = create_step_with_target(step.model_dump(), 1)
    assert payload["targetType"]["workoutTargetTypeKey"] == "speed.zone"
    # 1000/320 = 3.125 -> 3.12 (Python round to even), 1000/300 = 3.333 -> 3.33
    assert payload["targetType"]["targetValueOne"] == 3.12
    assert payload["targetType"]["targetValueTwo"] == 3.33
    
    # Power Target
    power = PowerTarget(min_watts=200, max_watts=250)
    step = WorkoutStep(type="run", duration_mins=30, target=power)
    payload = create_step_with_target(step.model_dump(), 1)
    assert payload["targetType"]["workoutTargetTypeKey"] == "power.zone"
    assert payload["targetType"]["targetValueOne"] == 200

def test_distance_duration_mapping():
    step = WorkoutStep(type="run", distance_m=800)
    payload = create_step_with_target(step.model_dump(), 1)
    assert payload["endCondition"]["conditionTypeKey"] == "distance"
    assert payload["endCondition"]["conditionTypeId"] == 3
    assert payload["endConditionValue"] == 800

def test_repeat_group_logic():
    steps = [
        WorkoutStep(type="run", distance_m=400, target=PaceTarget(min_pace_seconds=240, max_pace_seconds=250)),
        WorkoutStep(type="recovery", duration_mins=1)
    ]
    repeat = RepeatGroup(iterations=10, steps=steps)
    
    template = WorkoutTemplate(
        name="10x400m",
        date="2026-05-10",
        duration=60,
        steps=[
            WorkoutStep(type="warmup", duration_mins=10),
            repeat,
            WorkoutStep(type="cooldown", duration_mins=10)
        ]
    )
    
    workout_payload = create_workout(template.model_dump())
    
    # Check structure
    steps_payload = workout_payload["workoutSegments"][0]["workoutSteps"]
    assert len(steps_payload) == 3
    assert steps_payload[0]["stepType"]["stepTypeKey"] == "warmup"
    
    repeat_step = steps_payload[1]
    assert repeat_step["type"] == "RepeatStepDTO"
    assert repeat_step["numberOfIterations"] == 10
    assert len(repeat_step["workoutSteps"]) == 2
    assert repeat_step["workoutSteps"][0]["endCondition"]["conditionTypeKey"] == "distance"

def test_legacy_support():
    # Legacy duration field
    step = WorkoutStep(type="warmup", duration=10.0)
    assert step.duration == 10.0
    
    # Legacy target dictionary
    legacy_target = {"workoutTargetTypeKey": "heart.rate.zone", "targetValueOne": 140}
    step = WorkoutStep(type="run", duration_mins=30, target=legacy_target)
    payload = create_step_with_target(step.model_dump(), 1)
    assert payload["targetType"]["targetValueOne"] == 140
