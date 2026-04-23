#!/usr/bin/env python3
"""
Garmin Connect Workout Uploader with Cloudflare bypass
Adds delays between login attempts and retries
"""

import json
import logging
import random
import time
from pathlib import Path
from typing import Any, Optional

from garminconnect.workout import (
    RunningWorkout,
    WorkoutSegment,
    ExecutableStep,
    create_cooldown_step,
    create_recovery_step,
    create_warmup_step,
)

from ..utils import (
    find_token_file,
    get_authenticated_client,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
    pace_to_ms,
    power_to_watts,
    validate_workouts_file,
)
from ..models.workouts import WorkoutPlan, WorkoutTemplate
from .calendar import clear_calendar_range, schedule_workout

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
log = logging.getLogger(__name__)

WORKOUTS_FILE = Path(__file__).parent / "workouts.json"


def get_client():
    """Get authenticated Garmin client."""
    token_path = find_token_file()
    
    if not token_path:
        log.error("No tokens found. Run: python3 garmin.py auth")
        import sys
        sys.exit(1)
    
    log.info(f"Using saved tokens from: {token_path}")
    return get_authenticated_client(token_path)


def load_workouts():
    """Load and validate workouts from JSON file."""
    if not WORKOUTS_FILE.exists():
        log.error(f"{WORKOUTS_FILE} not found!")
        return []
    
    valid, errors = validate_workouts_file(WORKOUTS_FILE)
    if not valid:
        log.error(f"Validation errors in {WORKOUTS_FILE}:")
        for err in errors:
            log.error(f"  - {err}")
        return []
        
    with open(WORKOUTS_FILE) as f:
        data = json.load(f)
        plan = WorkoutPlan(data)
    
    log.info(f"Loaded {len(plan.root)} workouts from {WORKOUTS_FILE}")
    return [w.model_dump() for w in plan.root]


WORKOUTS = load_workouts()


def create_step_with_target(step_type: str, duration: float, order: int, target: Optional[Any] = None) -> ExecutableStep:
    """Create a step with target values at step level."""
    step_type_map = {
        "warmup": {"stepTypeId": 1, "stepTypeKey": "warmup", "displayOrder": 1},
        "cooldown": {"stepTypeId": 2, "stepTypeKey": "cooldown", "displayOrder": 2},
        "run": {"stepTypeId": 3, "stepTypeKey": "interval", "displayOrder": 3},
        "interval": {"stepTypeId": 3, "stepTypeKey": "interval", "displayOrder": 3},
        "recovery": {"stepTypeId": 3, "stepTypeKey": "interval", "displayOrder": 3},
    }
    
    target_value_one = None
    target_value_two = None
    workout_target_type_id = 1
    workout_target_type_key = "no.target"
    display_order = 1

    if isinstance(target, str):
        # Handle string targets (pace or power)
        if ":" in target or "min/km" in target:
            # Pace target: Garmin expects range for pace usually, but we can set it to +/- 5s
            ms = pace_to_ms(target)
            if ms > 0:
                workout_target_type_id = 6 # Speed/Pace
                workout_target_type_key = "speed.zone"
                display_order = 6
                # Create a small range around the target pace (approx +/- 2%)
                target_value_one = ms * 0.98
                target_value_two = ms * 1.02
        elif target.endswith("W") or target.isdigit():
            watts = power_to_watts(target)
            if watts > 0:
                workout_target_type_id = 2 # Power
                workout_target_type_key = "power.zone"
                display_order = 2
                target_value_one = watts * 0.95
                target_value_two = watts * 1.05
    elif isinstance(target, dict):
        workout_target_type_id = target.get("workoutTargetTypeId", 1)
        workout_target_type_key = target.get("workoutTargetTypeKey", "no.target")
        display_order = target.get("displayOrder", 1)
        target_value_one = target.get("targetValueOne")
        target_value_two = target.get("targetValueTwo")
    
    return ExecutableStep(
        stepOrder=order,
        stepType=step_type_map.get(step_type, step_type_map["run"]),
        endCondition={
            "conditionTypeId": 2,
            "conditionTypeKey": "time",
            "displayOrder": 2,
            "displayable": True,
        },
        endConditionValue=duration,
        targetType={
            "workoutTargetTypeId": workout_target_type_id,
            "workoutTargetTypeKey": workout_target_type_key,
            "displayOrder": display_order,
        },
        targetValueOne=target_value_one,
        targetValueTwo=target_value_two,
    )


def create_workout(workout_data):
    """Create a RunningWorkout from workout data."""
    steps = []
    order = 1
    
    # workout_data is already a dict from model_dump()
    for step_data in workout_data["steps"]:
        # step_data is a dict if coming from Pydantic model_dump
        step_type = step_data["type"]
        duration = step_data["duration"]
        target = step_data.get("target")
        
        if step_type == "warmup":
            steps.append(create_warmup_step(float(duration), order))
            order += 1
        elif step_type == "cooldown":
            steps.append(create_cooldown_step(float(duration), order))
            order += 1
        elif step_type in ["run", "interval", "recovery"]:
            steps.append(create_step_with_target(step_type, float(duration), order, target))
            order += 1
            if step_type == "interval" and duration > 0:
                 # Auto-recovery if it's an interval step and duration > 0? 
                 # (Keeping original logic but maybe this should be explicit in template)
                 pass
    
    return RunningWorkout(
        workoutName=workout_data["name"],
        description=workout_data["description"],
        estimatedDurationInSecs=workout_data["duration"],
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType={"sportTypeId": 1, "sportTypeKey": "running"},
                workoutSteps=steps
            )
        ]
    )


def delete_workout(client, workout_id):
    """Delete a workout by ID."""
    try:
        client.delete_workout(workout_id)
        return True
    except Exception as e:
        log.error(f"Error deleting {workout_id}: {e}")
        return False


def clean_old_workouts(client, month_prefix=None):
    """Delete old workouts from previous plans (keeps newest version of each). Skips ATP (Garmin auto) plans."""
    log.info("Fetching all workouts...")
    
    try:
        all_workouts = client.get_workouts()
    except Exception as e:
        log.error(f"Error fetching workouts: {e}")
        return
    
    log.info(f"Found {len(all_workouts)} total workouts")
    
    # Separate ATP workouts (cannot delete) from normal workouts
    atp_workouts = [w for w in all_workouts if w.get("atpPlanId")]
    normal_workouts = [w for w in all_workouts if not w.get("atpPlanId")]
    
    log.info(f"Skipping {len(atp_workouts)} ATP (Garmin auto) workouts - cannot delete via API")
    
    # If month_prefix is "all" or clean_all (None), delete ALL normal workouts
    if month_prefix == "all" or month_prefix is None:
        to_delete = [w.get("workoutId") for w in normal_workouts]
        log.info(f"Deleting ALL {len(to_delete)} normal workouts...")
        for i, wid in enumerate(to_delete, 1):
            log.info(f"[{i}/{len(to_delete)}] Deleting {wid}...")
            if delete_workout(client, wid):
                time.sleep(0.5)
        log.info(f"Removed {len(to_delete)} workouts!")
        return
    
    # Otherwise, just clean duplicates (keep newest) by month prefix
    by_name: dict[str, Any] = {}
    for w in normal_workouts:
        name = w.get("workoutName", "")
        if month_prefix and not name.startswith(month_prefix):
            continue
        if name not in by_name:
            by_name[name] = []
        by_name[name].append(w)
    
    duplicates = {name: ws for name, ws in by_name.items() if len(ws) > 1}
    
    if not duplicates:
        log.info(f"No duplicate workouts found for '{month_prefix or 'all'}'!")
        return
    
    log.info(f"Found {len(duplicates)} old workout groups:")
    
    to_delete = []
    for name, workouts in sorted(duplicates.items()):
        log.info(f"{name}: {len(workouts)} copies")
        workouts_sorted = sorted(workouts, key=lambda x: x.get("workoutId", 0))
        keep = workouts_sorted[-1]
        delete = workouts_sorted[:-1]
        
        log.info(f"Keeping: ID {keep.get('workoutId')} (newer)")
        for w in delete:
            log.info(f"Deleting: ID {w.get('workoutId')}")
            to_delete.append(w.get("workoutId"))
    
    if not to_delete:
        log.info("No duplicates to delete!")
        return
    
    log.info(f"Deleting {len(to_delete)} duplicate workouts...")
    for i, wid in enumerate(to_delete, 1):
        log.info(f"[{i}/{len(to_delete)}] Deleting {wid}...")
        if delete_workout(client, wid):
            time.sleep(0.5)
    
    log.info(f"Removed {len(to_delete)} old workouts!")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Garmin Workout Uploader")
    parser.add_argument("--clean", metavar="MONTH", help="Remove old workouts by name prefix (e.g., Apr, May)")
    parser.add_argument("--clean-all", action="store_true", help="Remove ALL normal workouts from library")
    parser.add_argument("--clear-range", nargs=2, metavar=("START", "END"), help="Clear calendar range and delete workouts (YYYY-MM-DD)")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--list", action="store_true", help="List all workouts in library")
    parser.add_argument("--delete", metavar="ID", help="Delete a specific workout by ID")
    args = parser.parse_args()
    
    log.info("Garmin Connect Workout Manager")
    log.info("=" * 40)
    
    client = get_client()
    
    if args.clear_range:
        start, end = args.clear_range
        if not args.yes:
            resp = input(f"Delete ALL workouts from calendar and account between {start} and {end}? [y/N] ")
            if resp.lower() != 'y':
                log.info("Cancelled.")
                return
        clear_calendar_range(client, start, end)
        return

    if args.clean or args.clean_all:
        prefix = None if args.clean_all else args.clean
        if not args.yes:
            resp = input(f"Delete old workouts{' for ' + prefix if prefix else ''} from library? [y/N] ")
            if resp.lower() != 'y':
                log.info("Cancelled.")
                return
        clean_old_workouts(client, prefix)
        return
    
    if args.list:
        workouts = client.get_workouts()
        log.info(f"{len(workouts)} total workouts in library:")
        for w in sorted(workouts, key=lambda x: x.get("workoutName", "")):
            log.info(f"  {w.get('workoutName')} (ID: {w.get('workoutId')})")
        return
    
    if args.delete:
        log.info(f"Deleting workout {args.delete}...")
        if delete_workout(client, args.delete):
            log.info("Deleted!")
        return
    
    log.info("Uploading and scheduling workouts...")
    
    # 1. Fetch current calendar to avoid duplicates
    months_to_fetch = set()
    for w in WORKOUTS:
        date_parts = w["date"].split("-")
        months_to_fetch.add((int(date_parts[0]), int(date_parts[1])))
    
    scheduled_dates = set()
    for year, month in months_to_fetch:
        try:
            cal = client.get_scheduled_workouts(year, month)
            if cal and "calendarItems" in cal:
                for item in cal["calendarItems"]:
                    if item.get("itemType") == "workout":
                        scheduled_dates.add(item.get("date"))
        except Exception as e:
            log.warning(f"Could not fetch calendar for {year}-{month}: {e}")

    # 2. Upload and Schedule
    for i, workout_data in enumerate(WORKOUTS, 1):
        log.info(f"[{i}/{len(WORKOUTS)}] {workout_data['name']} on {workout_data['date']}")
        
        if workout_data["date"] in scheduled_dates:
            log.info("Already scheduled on this date, skipping.")
            continue
            
        try:
            workout = create_workout(workout_data)
            
            result = client.upload_running_workout(workout)
            workout_id = result.get("workoutId") or result[0].get("workoutId")
            log.info(f"Uploaded (ID: {workout_id})")
            
            time.sleep(REQUEST_DELAY_MIN + random.uniform(0, REQUEST_DELAY_MAX - REQUEST_DELAY_MIN))
            
            schedule_workout(client, workout_id, workout_data["date"])
            log.info("Scheduled")
            
            time.sleep(REQUEST_DELAY_MIN + random.uniform(0, REQUEST_DELAY_MAX - REQUEST_DELAY_MIN))
            
        except Exception as e:
            log.error(f"Error: {e}")
            continue
    
    log.info("Done!")


if __name__ == "__main__":
    main()
