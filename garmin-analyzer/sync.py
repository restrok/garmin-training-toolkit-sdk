#!/usr/bin/env python3
"""
Workout Sync
Downloads completed workouts from Garmin Connect to compare with planned workouts.
"""

import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
log = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent))  # noqa: E402

from garmin_utils import (  # noqa: E402
    find_token_file,
    get_authenticated_client,
    REQUEST_DELAY_MIN,
)


def fetch_completed_workouts(client, days: int = 30) -> list[dict]:
    """Fetch completed activities from Garmin Connect."""
    log.info(f"Fetching completed workouts for last {days} days...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    activities = []
    
    try:
        data = client.get_activities(0, 200)
        
        for a in data:
            activity_date = a.get("startTimeLocal", "")
            if activity_date and activity_date[:10] < start_date.strftime("%Y-%m-%d"):
                continue
            
            activity_type = a.get("activityType", {}).get("typeKey")
            if activity_type != "running":
                continue
            
            activities.append({
                "activity_id": a.get("activityId"),
                "name": a.get("activityName"),
                "type": activity_type,
                "date": activity_date,
                "duration_sec": a.get("duration"),
                "distance_m": a.get("distance"),
                "avg_hr": a.get("averageHR"),
                "max_hr": a.get("maxHR"),
                "avg_pace": a.get("averageSpeed"),
                "calories": a.get("calories"),
                "elevation_gain": a.get("elevationGain"),
                "vo2max": a.get("vO2MaxValue"),
            })
            
    except Exception as e:
        log.error(f"Error fetching activities: {e}")
    
    log.info(f"Found {len(activities)} completed running activities")
    return activities


def sync_to_database(activities: list[dict]):
    """Sync completed activities to local database."""
    from garmin_analyzer.database import save_activities
    
    if activities:
        save_activities(activities)
        log.info(f"Synced {len(activities)} activities to database")


def match_completed_to_planned(completed: list[dict], planned: list[dict]) -> list[dict]:
    """Match completed activities to planned workouts by date proximity."""
    matches = []
    
    for planned_workout in planned:
        planned_date = planned_workout.get("date", "")
        if not planned_date:
            continue
        
        # Find completed activity on same date or nearby
        best_match = None
        best_distance_days = 999
        
        for activity in completed:
            act_date = activity.get("date", "")[:10]
            if not act_date:
                continue
            
            try:
                act_dt = datetime.strptime(act_date, "%Y-%m-%d")
                plan_dt = datetime.strptime(planned_date, "%Y-%m-%d")
                distance_days = abs((act_dt - plan_dt).days)
                
                if distance_days <= 1 and distance_days < best_distance_days:
                    best_distance_days = distance_days
                    best_match = activity
            except ValueError:
                continue
        
        if best_match:
            matches.append({
                "planned": planned_workout,
                "completed": best_match,
                "match_type": "same_day" if best_distance_days == 0 else "adjacent_day"
            })
    
    return matches


def get_training_status(client, date: str = None) -> dict:
    """Get training status from Garmin."""
    date = date or datetime.now().strftime("%Y-%m-%d")
    
    try:
        status = client.get_training_status()
        return status if status else {}
    except Exception as e:
        log.warning(f"Could not fetch training status: {e}")
        return {}


def get_recovery_status(client, date: str = None) -> dict:
    """Get recovery/readiness status."""
    date = date or datetime.now().strftime("%Y-%m-%d")
    
    result = {
        "training_readiness": None,
        "hrv": None,
        "resting_hr": None,
    }
    
    try:
        readiness = client.get_morning_training_readiness(date)
        if readiness and isinstance(readiness, list):
            latest = readiness[-1]
            result["training_readiness"] = {
                "value": latest.get("trainingReadinessValue"),
                "status": latest.get("trainingReadinessStatus"),
            }
    except Exception as e:
        log.warning(f"Could not fetch training readiness: {e}")
    
    time.sleep(REQUEST_DELAY_MIN)
    
    try:
        hrv = client.get_hrv_data(date)
        if hrv and isinstance(hrv, list) and hrv:
            latest = hrv[-1]
            result["hrv"] = {
                "avg": latest.get("averageHRV"),
                "min": latest.get("minHRV"),
                "max": latest.get("maxHRV"),
            }
    except Exception as e:
        log.warning(f"Could not fetch HRV: {e}")
    
    return result


def print_sync_summary(completed: list[dict], matched: list[dict]):
    """Print sync summary."""
    print("\n" + "=" * 50)
    print("WORKOUT SYNC SUMMARY")
    print("=" * 50)
    
    print(f"\n📥 Downloaded: {len(completed)} running activities")
    
    if matched:
        print(f"\n🔗 Matched to planned: {len(matched)} workouts")
        for m in matched[:5]:
            planned = m["planned"].get("name", "Unknown")
            completed_date = m["completed"].get("date", "")[:10]
            dist = m["completed"].get("distance_m", 0) / 1000
            print(f"  ✓ {planned} → {completed_date} ({dist:.1f} km)")
    else:
        print("\n⚠ No matches found (no planned workouts in database)")
    
    print("\n" + "=" * 50)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Workout Sync")
    parser.add_argument("--days", type=int, default=30, help="Days to fetch")
    parser.add_argument("--status", action="store_true", help="Show recovery/training status")
    args = parser.parse_args()
    
    log.info("Garmin Workout Sync")
    log.info("=" * 40)
    
    token_file = find_token_file()
    if not token_file:
        log.error("Not authenticated. Run garmin_auth_browser.py first.")
        return
    
    client = get_authenticated_client(token_file)
    
    try:
        client.login()
    except Exception as e:
        log.error(f"Login failed: {e}")
        return
    
    # Fetch completed activities
    completed = fetch_completed_workouts(client, args.days)
    
    # Sync to database
    sync_to_database(completed)
    
    # Get training status if requested
    if args.status:
        recovery = get_recovery_status(client)
        training = get_training_status(client)
        
        print("\n📊 Recovery Status")
        if recovery.get("training_readiness"):
            tr = recovery["training_readiness"]
            print(f"  Readiness: {tr.get('value')} ({tr.get('status')})")
        
        if recovery.get("hrv"):
            hrv = recovery["hrv"]
            print(f"  HRV: {hrv.get('avg')} ms (avg)")
        
        if training:
            print("\n📈 Training Status")
            if isinstance(training, dict):
                print(f"  Status: {training.get('trainingStatusLabel', 'N/A')}")
                print(f"  Load: {training.get('currentDayAcuteLoad', 'N/A')}")
    
    # Print summary
    print_sync_summary(completed, [])


if __name__ == "__main__":
    main()
