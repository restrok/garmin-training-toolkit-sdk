#!/usr/bin/env python3
"""
Auto Training Plan Generator
Generates personalized training plans based on Garmin data and user preferences.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
log = logging.getLogger(__name__)


def calculate_training_weeks(goal_date: str) -> int:
    """Calculate weeks until race day."""
    goal = datetime.strptime(goal_date, "%Y-%m-%d")
    today = datetime.now()
    return max(1, (goal - today).days // 7)


def calculate_hr_zones(profile: dict) -> dict:
    """Calculate HR zones based on profile data."""
    if not profile or not profile.get("birth_date"):
        return {}
    
    try:
        birth = datetime.fromisoformat(profile["birth_date"].replace("Z", "+00:00"))
        age = (datetime.now() - birth.replace(tzinfo=None)).days // 365
    except:
        return {}
    
    # Tanaka formula: 208 - 0.7 * age
    max_hr = int(208 - 0.7 * age)
    
    zones = {
        "max_hr": max_hr,
        "z1": (max_hr * 0.50, max_hr * 0.60),
        "z2": (max_hr * 0.60, max_hr * 0.70),
        "z3": (max_hr * 0.70, max_hr * 0.80),
        "z4": (max_hr * 0.80, max_hr * 0.90),
        "z5": (max_hr * 0.90, max_hr * 1.00),
    }
    log.info(f"Calculated HR zones based on age {age} (max HR: {max_hr})")
    return zones


def generate_plan(garmin_data: dict, prefs: dict) -> list[dict]:
    """Generate a training plan based on Garmin data and preferences."""
    
    # Get profile data
    profile = garmin_data.get("profile", {})
    hr_zones = calculate_hr_zones(profile)
    
    weight_kg = profile.get("weight") / 1000 if profile.get("weight") else None  # weight is in grams
    
    race_type = prefs.get("GOAL_RACE", "10K")
    goal_date = prefs.get("GOAL_DATE", "")
    training_days = int(prefs.get("TRAINING_DAYS", 3))
    max_session = int(prefs.get("MAX_SESSION_MINUTES", 90))
    
    target_pace = prefs.get("RACE_PACE_TARGET", "5:30")
    easy_pace = prefs.get("EASY_PACE", "6:00")
    tempo_pace = prefs.get("TEMPO_PACE", "5:45")
    interval_pace = prefs.get("INTERVAL_PACE", "5:15")
    
    weeks = calculate_training_weeks(goal_date)
    log.info(f"Generating {weeks}-week {race_type} training plan...")
    
    workouts = []
    
    # Parse target pace to seconds/km
    def pace_to_seconds(pace_str):
        parts = pace_str.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    
    target_sec = pace_to_seconds(target_pace)
    easy_sec = pace_to_seconds(easy_pace)
    tempo_sec = pace_to_seconds(tempo_pace)
    interval_sec = pace_to_seconds(interval_pace)
    
    # Determine phase lengths
    build_weeks = max(4, weeks - 4)  # Build phase
    peak_weeks = 2  # Peak/taper phase
    race_week = weeks  # Race week
    
    start_date = datetime.now() + timedelta(days=7)  # Start next week
    
    for week in range(1, weeks + 1):
        week_type = "base"
        if week >= build_weeks:
            week_type = "peak"
        if week == race_week:
            week_type = "race"
        
        # Deload every 4th week
        is_deload = (week % 4 == 0) and week < weeks
        
        # Generate workouts for this week
        if is_deload:
            # Deload week - reduce volume by 50%
            day = start_date + timedelta(weeks=week-1)
            workouts.append({
                "name": f"Easy Run {week}",
                "date": day.strftime("%Y-%m-%d"),
                "description": f"Easy recovery run - deload week",
                "duration": 30 * 60,
                "steps": [
                    ["warmup", 600, None],
                    ["run", 1500, None],
                    ["cooldown", 300, None],
                ]
            })
            if training_days > 1:
                day = start_date + timedelta(weeks=week-1, days=3)
                workouts.append({
                    "name": f"Easy {week}",
                    "date": day.strftime("%Y-%m-%d"),
                    "description": "Easy recovery run",
                    "duration": 20 * 60,
                    "steps": [
                        ["warmup", 300, None],
                        ["run", 600, None],
                        ["cooldown", 300, None],
                    ]
                })
        else:
            # Week structure: easy, tempo/interval, easy/long
            day = start_date + timedelta(weeks=week-1, days=0)  # Monday
            workouts.append({
                "name": f"Easy Run {week}",
                "date": day.strftime("%Y-%m-%d"),
                "description": f"Easy pace {easy_pace}/km - building aerobic base",
                "duration": 40 * 60,
                "steps": [
                    ["warmup", 600, None],
                    ["run", 1800, None],
                    ["cooldown", 300, None],
                ]
            })
            
            if training_days >= 2:
                day = start_date + timedelta(weeks=week-1, days=2)  # Wednesday
                if week <= build_weeks - 2:
                    # Tempo run
                    tempo_dist = min(3600 + week * 300, 5400)  # Progressively longer
                    workouts.append({
                        "name": f"Tempo Run {week}",
                        "date": day.strftime("%Y-%m-%d"),
                        "description": f"Tempo run at {tempo_pace}/km",
                        "duration": int(tempo_dist / tempo_sec * 60) + 600,
                        "steps": [
                            ["warmup", 600, None],
                            ["run", tempo_dist, None],
                            ["cooldown", 300, None],
                        ]
                    })
                else:
                    # Interval workout
                    interval_count = 4 + (week // 4)
                    interval_dur = 300 + (week * 30)
                    recovery_dur = 90
                    steps = [["warmup", 600, None]]
                    for i in range(interval_count):
                        steps.append(["run", interval_dur, None])
                        if i < interval_count - 1:
                            steps.append(["recovery", recovery_dur, None])
                    steps.append(["cooldown", 300, None])
                    
                    workouts.append({
                        "name": f"Intervals {week}",
                        "date": day.strftime("%Y-%m-%d"),
                        "description": f"{interval_count}x{interval_dur//60}min at {interval_pace}/km",
                        "duration": 600 + interval_count * interval_dur + (interval_count-1) * recovery_dur,
                        "steps": steps
                    })
            
            if training_days >= 3:
                day = start_date + timedelta(weeks=week-1, days=4)  # Friday
                long_dist = min(1800 + week * 300, 7200)
                workouts.append({
                    "name": f"Long Run {week}",
                    "date": day.strftime("%Y-%m-%d"),
                    "description": f"Long run at easy pace {easy_pace}/km",
                    "duration": int(long_dist / easy_sec * 60) + 600,
                    "steps": [
                        ["warmup", 900, None],
                        ["run", long_dist, None],
                        ["cooldown", 300, None],
                    ]
                })
            
            if training_days >= 4:
                day = start_date + timedelta(weeks=week-1, days=6)  # Sunday
                workouts.append({
                    "name": f"Pace Run {week}",
                    "date": day.strftime("%Y-%m-%d"),
                    "description": f"Practice race pace {target_pace}/km",
                    "duration": 40 * 60,
                    "steps": [
                        ["warmup", 600, None],
                        ["run", 1800, None],
                        ["cooldown", 300, None],
                    ]
                })
        
        log.info(f"Week {week}: {week_type}, {len([w for w in workouts if w['date'].startswith((start_date + timedelta(weeks=week-1)).strftime('%Y-%m-%d'))])} workouts")
    
    return workouts


def save_plan(workouts: list, output_path: Path):
    """Save generated plan to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(workouts, f, indent=2)
    log.info(f"Plan saved to {output_path}")


def main():
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from garmin_utils import load_env_file, find_token_file, get_authenticated_client
    from collector import collect_all_data
    
    log.info("Auto Training Plan Generator")
    log.info("=" * 40)
    
    # Load preferences
    prefs = load_env_file()
    
    if not prefs.get("GOAL_DATE"):
        log.error("GOAL_DATE not set in .env")
        sys.exit(1)
    
    # Collect fresh data if needed
    report_file = Path(__file__).parent / "data" / "garmin_report.json"
    if report_file.exists():
        with open(report_file) as f:
            garmin_data = json.load(f)
        log.info("Using cached data from report")
    else:
        log.info("Collecting fresh data...")
        token_file = find_token_file()
        if not token_file:
            log.error("Not authenticated. Run garmin_auth_browser.py first.")
            sys.exit(1)
        client = get_authenticated_client(token_file)
        garmin_data = collect_all_data(client, days=90)
    
    # Generate plan
    workouts = generate_plan(garmin_data, prefs)
    
    # Save
    output = Path(__file__).parent.parent / "garmin-workout-uploader" / "workouts.json"
    save_plan(workouts, output)
    
    log.info(f"Generated {len(workouts)} workouts")
    log.info("Run garmin_workout_uploader.py to upload to Garmin Connect")


if __name__ == "__main__":
    main()
