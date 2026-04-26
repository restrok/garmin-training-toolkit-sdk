#!/usr/bin/env python3
"""
Garmin Connect Workout Uploader with Cloudflare bypass
Returns raw dictionaries to prevent library-level Pydantic filtering of nested fields.
"""

import json
import logging
import random
import time
from pathlib import Path
from typing import Any, Optional, Dict

from ..utils import (
    find_token_file,
    get_authenticated_client,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
    pace_to_ms,
    power_to_watts,
    validate_workouts_file,
)
from ..protocol.workouts import WorkoutPlan
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
        log.debug(f"{WORKOUTS_FILE} not found (skipping load)")
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


def create_step(
    step_order: int,
    step_type_key: str,
    duration_value: float,
    condition_type_key: str = "time",
    condition_type_id: int = 2,
    target_type_id: int = 1,
    target_type_key: str = "no.target",
    target_value_one: Optional[float] = None,
    target_value_two: Optional[float] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a workout step as a raw dictionary.
    Implements TRIPLE REDUNDANCY for targets as required by Garmin API.
    """
    step_types = {
        "warmup": {"stepTypeId": 1, "stepTypeKey": "warmup", "displayOrder": 1},
        "cooldown": {"stepTypeId": 2, "stepTypeKey": "cooldown", "displayOrder": 2},
        "run": {"stepTypeId": 3, "stepTypeKey": "interval", "displayOrder": 3},
        "interval": {"stepTypeId": 3, "stepTypeKey": "interval", "displayOrder": 3},
        "recovery": {"stepTypeId": 4, "stepTypeKey": "recovery", "displayOrder": 4},
    }

    step_type = step_types.get(step_type_key, step_types["run"])
    
    step = {
        "type": "ExecutableStepDTO",
        "stepOrder": step_order,
        "stepType": step_type,
        "childStepId": None,
        "description": description,
        "endCondition": {
            "conditionTypeId": condition_type_id,
            "conditionTypeKey": condition_type_key,
            "displayOrder": condition_type_id,
            "displayable": True,
        },
        "endConditionValue": duration_value,
        "targetType": {
            "workoutTargetTypeId": target_type_id,
            "workoutTargetTypeKey": target_type_key,
            "displayOrder": target_type_id, # Usually matches ID or key order
        },
        "targetValueOne": target_value_one,
        "targetValueTwo": target_value_two,
        "zone": {"low": target_value_one, "high": target_value_two} if target_value_one is not None else None
    }
    
    return step


def create_step_with_target(step_data: Dict[str, Any], order: int) -> Dict[str, Any]:
    """Create a step with target values parsed from template."""
    step_type = step_data["type"]
    target = step_data.get("target")
    
    # Handle Durations (Convert Minutes to Seconds)
    duration_value = 0.0
    condition_type_key = "time"
    condition_type_id = 2
    
    if step_data.get("distance_m") is not None:
        duration_value = float(step_data["distance_m"])
        condition_type_key = "distance"
        condition_type_id = 3
    elif step_data.get("duration_mins") is not None:
        duration_value = float(step_data["duration_mins"]) * 60
    elif step_data.get("duration") is not None:
        duration_value = float(step_data["duration"]) * 60

    target_value_one = None
    target_value_two = None
    workout_target_type_id = 1
    workout_target_type_key = "no.target"

    if isinstance(target, str):
        # Handle string targets (pace or power)
        if ":" in target or "min/km" in target:
            ms = pace_to_ms(target)
            if ms > 0:
                workout_target_type_id = 5 # speed.zone (pace)
                workout_target_type_key = "speed.zone"
                # +/- 2% range
                target_value_one = round(ms * 0.98, 2)
                target_value_two = round(ms * 1.02, 2)
        elif "-" in target and all(p.isdigit() for p in target.split("-")):
            # Handle HR range string "140-150"
            parts = target.split("-")
            workout_target_type_id = 4 # heart.rate.zone
            workout_target_type_key = "heart.rate.zone"
            target_value_one = float(parts[0])
            target_value_two = float(parts[1])
        elif target.endswith("W") or target.isdigit():
            watts = power_to_watts(target)
            if watts > 0:
                workout_target_type_id = 2 # power.zone
                workout_target_type_key = "power.zone"
                target_value_one = round(watts * 0.95, 2)
                target_value_two = round(watts * 1.05, 2)
    elif isinstance(target, dict):
        target_type = target.get("target_type") or target.get("workoutTargetTypeKey", "no.target")
        
        # New Explicit Models
        if target_type == "heart.rate":
            workout_target_type_id = 4
            workout_target_type_key = "heart.rate.zone"
            target_value_one = float(target["min_bpm"])
            target_value_two = float(target["max_bpm"])
        elif target_type == "pace":
            workout_target_type_id = 5
            workout_target_type_key = "speed.zone"
            # min_pace_seconds is e.g. 240 (4:00/km) which is 1000/240 = 4.16 m/s
            # Note: Pace in seconds/km. Higher seconds = slower speed.
            # targetValueOne is MIN speed (slower), targetValueTwo is MAX speed (faster)
            # So targetValueOne = 1000 / max_pace_seconds
            # and targetValueTwo = 1000 / min_pace_seconds
            target_value_one = round(1000.0 / target["max_pace_seconds"], 2)
            target_value_two = round(1000.0 / target["min_pace_seconds"], 2)
        elif target_type == "power":
            workout_target_type_id = 2
            workout_target_type_key = "power.zone"
            target_value_one = float(target["min_watts"])
            target_value_two = float(target["max_watts"])
        else:
            # Handle legacy Garmin-raw keys and our old Semantic keys
            # ID Mapping
            type_to_id = {
                "no.target": 1,
                "power.zone": 2,
                "heart.rate.zone": 4,
                "speed.zone": 5,
                "cadence.zone": 6
            }
            
            workout_target_type_key = target_type
            workout_target_type_id = target.get("target_type_id") or target.get("workoutTargetTypeId") or type_to_id.get(target_type, 1)
            
            target_value_one = target.get("min_target") or target.get("targetValueOne")
            target_value_two = target.get("max_target") or target.get("targetValueTwo")
    
    return create_step(
        step_order=order,
        step_type_key=step_type,
        duration_value=duration_value,
        condition_type_key=condition_type_key,
        condition_type_id=condition_type_id,
        target_type_id=workout_target_type_id,
        target_type_key=workout_target_type_key,
        target_value_one=target_value_one,
        target_value_two=target_value_two
    )


def create_workout(workout_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a Garmin workout as a raw dictionary instead of an object.
    Supports Repeat Groups and Distance-based steps.
    """
    steps = []
    current_order = 1
    
    for step_data in workout_data["steps"]:
        if step_data.get("type") == "repeat":
            repeat_steps = []
            repeat_order = 1
            for sub_step in step_data["steps"]:
                repeat_steps.append(create_step_with_target(sub_step, repeat_order))
                repeat_order += 1
            
            steps.append({
                "type": "RepeatStepDTO",
                "stepOrder": current_order,
                "stepType": {"stepTypeId": 6, "stepTypeKey": "repeat", "displayOrder": 6},
                "childStepId": None,
                "numberOfIterations": step_data["iterations"],
                "repeatChildSteps": repeat_steps,  # Must be repeatChildSteps
                "smartRepeat": False,
                "endCondition": {
                    "conditionTypeId": 1,
                    "conditionTypeKey": "iterations",
                    "displayOrder": 1,
                    "displayable": True,
                },
                "endConditionValue": step_data["iterations"],
                "targetType": {
                    "workoutTargetTypeId": 1,
                    "workoutTargetTypeKey": "no.target",
                    "displayOrder": 1,
                },
                "targetValueOne": None,
                "targetValueTwo": None,
            })
        else:
            steps.append(create_step_with_target(step_data, current_order))
        
        current_order += 1
    
    estimated_duration = workout_data.get("duration")
    
    workout = {
        "workoutName": workout_data["name"],
        "description": workout_data.get("description", ""),
        "sportType": {"sportTypeId": 1, "sportTypeKey": "running"},
        "estimatedDurationInSecs": estimated_duration * 60 if estimated_duration is not None else None,
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": {"sportTypeId": 1, "sportTypeKey": "running"},
                "workoutSteps": steps
            }
        ]
    }
    
    return workout


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
    parser.add_argument("--clear-range", nargs=2, metavar=("START", "END"), help="Clear calendar range (YYYY-MM-DD)")
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
            resp = input(f"Unschedule ALL items from calendar between {start} and {end}? [y/N] ")
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
            
            # Using raw dictionary upload
            result = client.upload_workout(workout)
            workout_id = result.get("workoutId")
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
