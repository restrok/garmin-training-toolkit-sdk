#!/usr/bin/env python3
"""Garmin Connect Workout Uploader with Cloudflare bypass.

Returns raw dictionaries to prevent library-level Pydantic filtering of nested fields.
"""

import json
import logging
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from garminconnect import Garmin

from ..protocol.workouts import WorkoutPlan
from ..utils import (
    REQUEST_DELAY_MAX,
    REQUEST_DELAY_MIN,
    find_token_file,
    get_authenticated_client,
    pace_to_ms,
    power_to_watts,
    validate_workouts_file,
)
from .calendar import clear_calendar_range, get_calendar_range, schedule_workout

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

WORKOUTS_FILE = Path(__file__).parent / "workouts.json"


def get_client() -> Garmin:
    """Get authenticated Garmin client.

    Returns:
        An authenticated Garmin API client instance.
    """
    token_path = find_token_file()

    if not token_path:
        log.error("No tokens found. Run: python3 garmin.py auth")
        import sys

        sys.exit(1)

    log.info("Using saved tokens from: %s", token_path)
    return get_authenticated_client(token_path)


def load_workouts() -> List[Dict[str, Any]]:
    """Load and validate workouts from JSON file.

    Returns:
        A list of workout dictionaries.
    """
    if not WORKOUTS_FILE.exists():
        log.debug("%s not found (skipping load)", WORKOUTS_FILE)
        return []

    valid, errors = validate_workouts_file(WORKOUTS_FILE)
    if not valid:
        log.error("Validation errors in %s:", WORKOUTS_FILE)
        for err in errors:
            log.error("  - %s", err)
        return []

    with open(WORKOUTS_FILE) as f:
        data = json.load(f)
        plan = WorkoutPlan(data)

    log.info("Loaded %d workouts from %s", len(plan.root), WORKOUTS_FILE)
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
    """Create a workout step as a raw dictionary.

    Implements TRIPLE REDUNDANCY for targets as required by Garmin API.

    Args:
        step_order: The order of the step in the workout.
        step_type_key: The key representing the type of step (e.g., "warmup").
        duration_value: The value representing the duration of the step.
        condition_type_key: The key representing the end condition type.
        condition_type_id: The ID representing the end condition type.
        target_type_id: The ID representing the target type.
        target_type_key: The key representing the target type.
        target_value_one: The first target value (e.g., min bpm or pace).
        target_value_two: The second target value (e.g., max bpm or pace).
        description: Optional description for the step.

    Returns:
        A dictionary representing a workout step.
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
            "displayOrder": target_type_id,  # Usually matches ID or key order
        },
        "targetValueOne": target_value_one,
        "targetValueTwo": target_value_two,
        "zone": {"low": target_value_one, "high": target_value_two}
        if target_value_one is not None
        else None,
    }

    return step


def create_step_with_target(step_data: Dict[str, Any], order: int) -> Dict[str, Any]:
    """Create a step with target values parsed from template.

    Args:
        step_data: Dictionary containing step information.
        order: The order of the step.

    Returns:
        A dictionary representing a workout step with targets.
    """
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

    # Support Pydantic models by converting to dict
    if target is not None and hasattr(target, "model_dump"):
        target = target.model_dump()

    if isinstance(target, str):
        # Handle string targets (pace or power)
        if ":" in target or "min/km" in target:
            ms = pace_to_ms(target)
            if ms > 0:
                workout_target_type_id = 5  # speed.zone (pace)
                workout_target_type_key = "speed.zone"
                # +/- 2% range
                target_value_one = round(ms * 0.98, 2)
                target_value_two = round(ms * 1.02, 2)
        elif "-" in target and all(p.isdigit() for p in target.split("-")):
            # Handle HR range string "140-150"
            parts = target.split("-")
            workout_target_type_id = 4  # heart.rate.zone
            workout_target_type_key = "heart.rate.zone"
            target_value_one = float(parts[0])
            target_value_two = float(parts[1])
        elif target.endswith("W") or target.isdigit():
            watts = power_to_watts(target)
            if watts > 0:
                workout_target_type_id = 2  # power.zone
                workout_target_type_key = "power.zone"
                target_value_one = round(watts * 0.95, 2)
                target_value_two = round(watts * 1.05, 2)
    elif isinstance(target, dict):
        target_type = target.get("target_type") or target.get(
            "workoutTargetTypeKey", "no.target"
        )

        # New Explicit Models
        if target_type == "heart.rate":
            workout_target_type_id = 4
            workout_target_type_key = "heart.rate.zone"
            target_value_one = float(target["min_bpm"])
            target_value_two = float(target["max_bpm"])
        elif target_type == "pace":
            workout_target_type_id = 5
            workout_target_type_key = "speed.zone"
            # targetValueOne is MIN speed (slower), targetValueTwo is MAX speed (faster)
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
                "cadence.zone": 6,
            }

            workout_target_type_key = target_type
            workout_target_type_id = (
                target.get("target_type_id")
                or target.get("workoutTargetTypeId")
                or type_to_id.get(target_type, 1)
            )

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
        target_value_two=target_value_two,
    )


def create_workout(workout_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a Garmin workout as a raw dictionary instead of an object.

    Supports Repeat Groups (RepeatGroupDTO) and Distance-based steps.
    FIXED: Uses RepeatGroupDTO and workoutSteps to avoid InvalidTypeIdException.

    Args:
        workout_data: Dictionary containing workout information.

    Returns:
        A dictionary representing a complete Garmin workout.
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

            steps.append(
                {
                    "type": "RepeatGroupDTO",
                    "stepOrder": current_order,
                    "stepType": {
                        "stepTypeId": 6,
                        "stepTypeKey": "repeat",
                        "displayOrder": 6,
                    },
                    "numberOfIterations": step_data["iterations"],
                    "workoutSteps": repeat_steps,
                    "smartRepeat": False,
                    "endCondition": {
                        "conditionTypeId": 7,
                        "conditionTypeKey": "iterations",
                        "displayOrder": 7,
                        "displayable": True,
                    },
                    "endConditionValue": float(step_data["iterations"]),
                }
            )
        else:
            steps.append(create_step_with_target(step_data, current_order))

        current_order += 1

    estimated_duration = workout_data.get("duration")
    sport_type_key = workout_data.get("sport", "running").lower()

    # Garmin Sport Type Mapping
    sport_types = {
        "running": {"sportTypeId": 1, "sportTypeKey": "running"},
        "cycling": {"sportTypeId": 2, "sportTypeKey": "cycling"},
        "swimming": {"sportTypeId": 4, "sportTypeKey": "lap_swimming"},
        "lap_swimming": {"sportTypeId": 4, "sportTypeKey": "lap_swimming"},
    }
    sport_type = sport_types.get(sport_type_key, sport_types["running"])

    workout = {
        "workoutName": workout_data["name"],
        "description": workout_data.get("description", ""),
        "sportType": sport_type,
        "estimatedDurationInSecs": estimated_duration * 60
        if estimated_duration is not None
        else None,
        "workoutSegments": [
            {"segmentOrder": 1, "sportType": sport_type, "workoutSteps": steps}
        ],
    }

    # Pool Length for swimming
    if sport_type_key in ("swimming", "lap_swimming"):
        workout["poolLength"] = workout_data.get("pool_length", 25.0)
        workout["poolLengthUnit"] = {"unitId": 1, "unitKey": "meter"}

    return workout


def delete_workout(garmin_client: Garmin, workout_id: str) -> bool:
    """Delete a workout by ID.

    Args:
        garmin_client: The Garmin API client instance.
        workout_id: The ID of the workout to delete.

    Returns:
        True if successful, False otherwise.
    """
    try:
        garmin_client.delete_workout(workout_id)
        return True
    except Exception as e:
        log.error("Error deleting %s: %s", workout_id, e)
        return False


def clean_old_workouts(
    garmin_client: Garmin, month_prefix: Optional[str] = None
) -> None:
    """Delete old workouts from previous plans.

    Keeps newest version of each. Skips ATP (Garmin auto) plans.

    Args:
        garmin_client: The Garmin API client instance.
        month_prefix: Optional prefix to filter workouts by name.
    """
    log.info("Fetching all workouts...")

    try:
        all_workouts = garmin_client.get_workouts()
    except Exception as e:
        log.error("Error fetching workouts: %s", e)
        return

    log.info("Found %d total workouts", len(all_workouts))

    # Separate ATP workouts (cannot delete) from normal workouts
    atp_workouts = [w for w in all_workouts if w.get("atpPlanId")]
    normal_workouts = [w for w in all_workouts if not w.get("atpPlanId")]

    log.info(
        "Skipping %d ATP (Garmin auto) workouts - cannot delete via API",
        len(atp_workouts),
    )

    # If month_prefix is "all" or clean_all (None), delete ALL normal workouts
    if month_prefix == "all" or month_prefix is None:
        to_delete = [w.get("workoutId") for w in normal_workouts]
        log.info("Deleting ALL %d normal workouts...", len(to_delete))
        for i, wid in enumerate(to_delete, 1):
            log.info("[%d/%d] Deleting %s...", i, len(to_delete), wid)
            if delete_workout(garmin_client, wid):
                time.sleep(0.5)
        log.info("Removed %d workouts!", len(to_delete))
        return

    # Otherwise, just clean duplicates (keep newest) by month prefix
    by_name: Dict[str, Any] = {}
    for w in normal_workouts:
        name = w.get("workoutName", "")
        if month_prefix and not name.startswith(month_prefix):
            continue
        if name not in by_name:
            by_name[name] = []
        by_name[name].append(w)

    duplicates = {name: ws for name, ws in by_name.items() if len(ws) > 1}

    if not duplicates:
        log.info("No duplicate workouts found for '%s'!", month_prefix or "all")
        return

    log.info("Found %d old workout groups:", len(duplicates))

    to_delete_ids = []
    for name, workouts in sorted(duplicates.items()):
        log.info("%s: %d copies", name, len(workouts))
        workouts_sorted = sorted(workouts, key=lambda x: x.get("workoutId", 0))
        keep = workouts_sorted[-1]
        delete = workouts_sorted[:-1]

        log.info("Keeping: ID %s (newer)", keep.get("workoutId"))
        for w in delete:
            log.info("Deleting: ID %s", w.get("workoutId"))
            to_delete_ids.append(w.get("workoutId"))

    if not to_delete_ids:
        log.info("No duplicates to delete!")
        return

    log.info("Deleting %d duplicate workouts...", len(to_delete_ids))
    for i, wid in enumerate(to_delete_ids, 1):
        log.info("[%d/%d] Deleting %s...", i, len(to_delete_ids), wid)
        if delete_workout(garmin_client, wid):
            time.sleep(0.5)

    log.info("Removed %d old workouts!", len(to_delete_ids))


def main() -> None:
    """Main execution function for Garmin Workout Uploader."""
    import argparse

    parser = argparse.ArgumentParser(description="Garmin Workout Uploader")
    parser.add_argument(
        "--clean",
        metavar="MONTH",
        help="Remove old workouts by name prefix (e.g., Apr, May)",
    )
    parser.add_argument(
        "--clean-all",
        action="store_true",
        help="Remove ALL normal workouts from library",
    )
    parser.add_argument(
        "--clear-range",
        nargs=2,
        metavar=("START", "END"),
        help="Clear calendar range (YYYY-MM-DD)",
    )
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    parser.add_argument(
        "--list", action="store_true", help="List all workouts in library"
    )
    parser.add_argument(
        "--delete", metavar="ID", help="Delete a specific workout by ID"
    )
    args = parser.parse_args()

    log.info("Garmin Connect Workout Manager")
    log.info("=" * 40)

    garmin_client = get_client()

    if args.clear_range:
        start, end = args.clear_range
        if not args.yes:
            resp = input(
                f"Unschedule ALL items from calendar between {start} and {end}? [y/N] "
            )
            if resp.lower() != "y":
                log.info("Cancelled.")
                return
        clear_calendar_range(garmin_client, start, end)
        return

    if args.clean or args.clean_all:
        prefix = None if args.clean_all else args.clean
        if not args.yes:
            resp = input(
                f"Delete old workouts{' for ' + prefix if prefix else ''} from library? [y/N] "
            )
            if resp.lower() != "y":
                log.info("Cancelled.")
                return
        clean_old_workouts(garmin_client, prefix)
        return

    if args.list:
        workouts = garmin_client.get_workouts()
        log.info("%d total workouts in library:", len(workouts))
        for w in sorted(workouts, key=lambda x: x.get("workoutName", "")):
            log.info("  %s (ID: %s)", w.get("workoutName"), w.get("workoutId"))
        return

    if args.delete:
        log.info("Deleting workout %s...", args.delete)
        if delete_workout(garmin_client, args.delete):
            log.info("Deleted!")
        return

    log.info("Uploading and scheduling workouts...")

    # 1. Fetch current calendar to avoid duplicates
    scheduled_dates = set()
    if WORKOUTS:
        try:
            dates = [w["date"] for w in WORKOUTS]
            start_date = min(dates)
            end_date = max(dates)

            log.info(
                "Checking calendar for duplicates between %s and %s...",
                start_date,
                end_date,
            )
            items = get_calendar_range(garmin_client, start_date, end_date)
            for item in items:
                if item.get("itemType") == "workout":
                    scheduled_dates.add(item.get("date"))
        except Exception as e:
            log.warning("Could not fetch calendar to check for duplicates: %s", e)

    # 2. Upload and Schedule
    for i, workout_data in enumerate(WORKOUTS, 1):
        log.info(
            "[%d/%d] %s on %s",
            i,
            len(WORKOUTS),
            workout_data["name"],
            workout_data["date"],
        )

        if workout_data["date"] in scheduled_dates:
            log.info("Already scheduled on this date, skipping.")
            continue

        try:
            workout = create_workout(workout_data)
            log.debug("Uploading workout payload: %s", json.dumps(workout, indent=2))

            # Using raw dictionary upload
            result = garmin_client.upload_workout(workout)
            workout_id = result.get("workoutId")
            log.info("Uploaded (ID: %s)", workout_id)

            time.sleep(
                REQUEST_DELAY_MIN
                + random.uniform(0, REQUEST_DELAY_MAX - REQUEST_DELAY_MIN)
            )

            schedule_workout(garmin_client, workout_id, workout_data["date"])
            log.info("Scheduled")

            time.sleep(
                REQUEST_DELAY_MIN
                + random.uniform(0, REQUEST_DELAY_MAX - REQUEST_DELAY_MIN)
            )

        except Exception as e:
            log.error("Error: %s", e)
            continue

    log.info("Done!")


if __name__ == "__main__":
    main()
