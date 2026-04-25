import pytest
from garmin_training_toolkit_sdk.models.workouts import (
    WorkoutTarget, 
    WorkoutStep, 
    WorkoutTemplate,
    create_simple_hr_workout,
    create_simple_pace_workout
)
from garmin_training_toolkit_sdk.uploaders.workouts import create_step_with_target

def test_workout_target_validation():
    # Valid HR target
    target = WorkoutTarget(target_type="heart.rate.zone", min_target=140, max_target=160)
    assert target.min_target == 140
    
    # Invalid HR target
    with pytest.raises(ValueError, match="Heart rate value 300.0 is outside realistic range"):
        WorkoutTarget(target_type="heart.rate.zone", min_target=300)

def test_semantic_to_garmin_mapping():
    # Test dictionary with semantic keys
    semantic_target = {
        "target_type": "heart.rate.zone",
        "min_target": 145,
        "max_target": 155
    }
    
    step = create_step_with_target("run", 30.0, 1, semantic_target)
    
    # Check if mapped correctly to Garmin format
    assert step["targetType"]["workoutTargetTypeKey"] == "heart.rate.zone"
    assert step["targetType"]["workoutTargetTypeId"] == 4
    assert step["targetType"]["targetValueOne"] == 145
    assert step["targetType"]["targetValueTwo"] == 155

def test_quick_start_helpers():
    # HR Workout
    workout = create_simple_hr_workout(
        name="LLM Test Workout",
        date="2026-05-01",
        bpm_min=140,
        bpm_max=150,
        duration_mins=40
    )
    
    assert workout.name == "LLM Test Workout"
    assert len(workout.steps) == 3 # warmup, run, cooldown
    assert workout.steps[1].target.min_target == 140
    
    # Pace Workout
    workout_pace = create_simple_pace_workout(
        name="Pace Test",
        date="2026-05-02",
        pace="5:00",
        duration_mins=20
    )
    assert workout_pace.steps[1].target == "5:00"

def test_alias_compatibility():
    # Test that we can still use Garmin names if needed
    target = WorkoutTarget(workoutTargetTypeKey="heart.rate.zone", targetValueOne=140)
    assert target.target_type == "heart.rate.zone"
    assert target.min_target == 140
