#!/usr/bin/env python3
"""
Garmin Connect Data Collector
Fetches all available data from Garmin Connect and generates a report.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from garmin_utils import (
    find_token_file,
    get_authenticated_client,
    load_env_file,
    REQUEST_DELAY_MIN,
)

# Local race predictions (fallback when Garmin API fails)
def calculate_local_predictions(running_activities: list) -> dict:
    """Calculate race predictions from activity data using Riegel formula."""
    if not running_activities:
        return {}
    
    results = []
    for a in running_activities:
        pace = a.get("avg_pace", 0)
        distance = a.get("distance_m", 0) / 1000
        if pace > 0 and distance >= 5:
            sec_km = 1000 / pace
            results.append({"pace": sec_km, "distance": distance})
    
    if not results:
        return {}
    
    # Use median of best 3 runs
    results.sort(key=lambda x: x["pace"])
    best_3 = results[:3]
    median_pace = sorted([r["pace"] for r in best_3])[1]
    
    # Riegel: T2 = T1 * (D2/D1)^1.06
    # Use 10K as baseline
    baseline_dist = 10
    baseline_time = median_pace * baseline_dist
    
    race_distances = {"5K": 5, "10K": 10, "Half": 21.1, "Marathon": 42.2}
    predictions = {}
    for race, dist in race_distances.items():
        time_sec = baseline_time * (dist / baseline_dist) ** 1.06
        predictions[race] = int(time_sec)
    
    return predictions

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
log = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent / "data"
REPORT_FILE = OUTPUT_DIR / "garmin_report.json"


def format_duration(seconds: float) -> str:
    """Format seconds to hh:mm:ss or mm:ss depending on duration."""
    total_sec = int(seconds)
    if total_sec >= 3600:
        return f"{total_sec//3600}:{(total_sec%3600)//60:02d}:{total_sec%60:02d}"
    return f"{total_sec//60}:{total_sec%60:02d}"


def format_pace(m_per_sec: float) -> str:
    """Format pace from m/s to min:sec/km."""
    if m_per_sec <= 0:
        return "--:--"
    sec_per_km = int(1000 / m_per_sec)
    mins = sec_per_km // 60
    secs = sec_per_km % 60
    return f"{mins}:{secs:02d}"


def get_activity_splits(client, activity_id: int) -> list:
    """Fetch detailed splits for an activity."""
    try:
        splits = client.get_activity_splits(activity_id)
        if splits and "lapDTOs" in splits:
            laps = []
            for lap in splits["lapDTOs"]:
                laps.append({
                    "index": lap.get("lapIndex"),
                    "type": lap.get("intensityType"),
                    "distance_m": lap.get("distance"),
                    "duration_sec": lap.get("duration"),
                    "moving_duration_sec": lap.get("movingDuration"),
                    "avg_hr": lap.get("averageHR"),
                    "max_hr": lap.get("maxHR"),
                    "avg_pace_mps": lap.get("averageMovingSpeed"),  # m/s
                    "avg_cadence": lap.get("averageRunCadence"),
                    "calories": lap.get("calories"),
                })
            return laps
    except Exception as e:
        log.warning(f"Failed to get splits for {activity_id}: {e}")
    return []


def load_user_preferences():
    """Load user training preferences from .env file."""
    return load_env_file()


def get_client():
    """Get authenticated Garmin client with auto-refresh."""
    token_file = find_token_file()
    if not token_file:
        raise Exception("Not authenticated. Run: python3 garmin.py auth")
    
    log.info(f"Using tokens from: {token_file}")
    client = get_authenticated_client(token_file)
    return client


def collect_all_data(client, days=90):
    """Collect all data from Garmin Connect."""
    log.info(f"Collecting data for the last {days} days...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    data = {
        "collection_date": datetime.now().isoformat(),
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "profile": {},
        "activities": [],
        "sleep": [],
        "body": [],
        "metrics": {},
        "personal_records": {},
        "race_predictions": {},
        "fitness_age": [],
        "hrv": [],
        "training_readiness": [],
        "steps": [],
        "stress": [],
    }
    
    # Profile
    log.info("Fetching profile...")
    try:
        profile = client.get_user_profile()
        user_data = profile.get("userData", {})
        data["profile"] = {
            "gender": user_data.get("gender"),
            "birth_date": user_data.get("birthDate"),
            "weight": user_data.get("weight"),  # grams
            "height": user_data.get("height"),  # cm
        }
        # Also get display name separately
        try:
            full_name = client.get_full_name()
            if full_name:
                data["profile"]["display_name"] = full_name
        except:
            pass
    except Exception as e:
        log.warning(f"Profile fetch failed: {e}")
    
    # Body composition (weight)
    log.info("Fetching body composition...")
    try:
        body = client.get_body_composition(end_date.strftime("%Y-%m-%d"))
        if body and "dateWeightList" in body:
            weights = body["dateWeightList"]
            if weights:
                latest = weights[0]
                data["profile"]["weight"] = latest.get("weight", {}).get("value")
                data["body"] = weights[:30]
    except Exception as e:
        log.warning(f"Body composition fetch failed: {e}")
    
    time.sleep(REQUEST_DELAY_MIN)
    
    # Activities
    log.info("Fetching activities...")
    try:
        activities = client.get_activities(0, 200)
        for a in activities:
            # Filter by date range
            activity_date = a.get("startTimeLocal", "")
            if activity_date and activity_date[:10] < start_date.strftime("%Y-%m-%d"):
                continue
            
            activity_data = {
                "id": a.get("activityId"),
                "name": a.get("activityName"),
                "type": a.get("activityType", {}).get("typeKey"),
                "date": activity_date,
                "duration_sec": a.get("duration"),
                "distance_m": a.get("distance"),
                "avg_hr": a.get("averageHR"),
                "max_hr": a.get("maxHR"),
                "avg_pace": a.get("averageSpeed"),
                "calories": a.get("calories"),
                "elevation_gain": a.get("elevationGain"),
                "vo2max": a.get("vO2MaxValue"),
            }
            
            # Fetch splits for recent activities (last 5 to avoid rate limiting)
            if len(data["activities"]) < 5:
                try:
                    splits = get_activity_splits(client, a.get("activityId"))
                    if splits:
                        activity_data["splits"] = splits
                except:
                    pass
            
            data["activities"].append(activity_data)
    except Exception as e:
        log.warning(f"Activities fetch failed: {e}")
    
    time.sleep(REQUEST_DELAY_MIN)
    
    # Sleep data
    log.info("Fetching sleep data...")
    try:
        sleep_data = client.get_sleep_data(
            start_date.strftime("%Y-%m-%d"), 
            end_date.strftime("%Y-%m-%d")
        )
        if sleep_data:
            for s in sleep_data:
                data["sleep"].append({
                    "date": s.get("calendarDate"),
                    "start": s.get("sleepStartTimestampGMT"),
                    "end": s.get("sleepEndTimestampGMT"),
                    "duration_sec": s.get("sleepTimeSeconds"),
                    "deep_sec": s.get("deepSleepSeconds", 0),
                    "light_sec": s.get("lightSleepSeconds", 0),
                    "rem_sec": s.get("remSleepSeconds", 0),
                    "awake_sec": s.get("awakeSleepSeconds", 0),
                    "quality": s.get("sleepWindowConfirmationType"),
                })
    except Exception as e:
        log.warning(f"Sleep data fetch failed: {e}")
    
    time.sleep(REQUEST_DELAY_MIN)
    
    # Race predictions
    log.info("Fetching race predictions...")
    try:
        races = client.get_race_predictions()
        if races:
            data["race_predictions"] = races[-1] if isinstance(races, list) else races
    except Exception as e:
        log.warning(f"Race predictions fetch failed: {e}")
    
    # Training status
    log.info("Fetching training status...")
    try:
        status = client.get_training_status()
        if status:
            data["metrics"]["training_status"] = status
    except Exception as e:
        log.warning(f"Training status fetch failed: {e}")
    
    time.sleep(REQUEST_DELAY_MIN)
    
    # HRV
    log.info("Fetching HRV data...")
    try:
        hrv = client.get_hrv_data(end_date.strftime("%Y-%m-%d"))
        if hrv and isinstance(hrv, list):
            for h in hrv:
                data["hrv"].append({
                    "date": h.get("calendarDate"),
                    "avg_hrv": h.get("averageHRV"),
                    "min_hrv": h.get("minHRV"),
                    "max_hrv": h.get("maxHRV"),
                })
    except Exception as e:
        log.warning(f"HRV data fetch failed: {e}")
    
    # Training readiness
    log.info("Fetching training readiness...")
    try:
        readiness = client.get_morning_training_readiness(end_date.strftime("%Y-%m-%d"))
        if readiness and isinstance(readiness, list):
            for r in readiness[-30:]:
                data["training_readiness"].append({
                    "date": r.get("calendarDate"),
                    "value": r.get("trainingReadinessValue"),
                    "status": r.get("trainingReadinessStatus"),
                })
    except Exception as e:
        log.warning(f"Training readiness fetch failed: {e}")
    
    # Max metrics (VO2 Max, etc.)
    log.info("Fetching max metrics...")
    try:
        metrics = client.get_max_metrics(end_date.strftime("%Y-%m-%d"))
        if metrics:
            data["metrics"]["max"] = metrics
            # Extract VO2 Max
            if "vo2MaxValue" in str(metrics):
                for m in metrics if isinstance(metrics, list) else []:
                    if "vo2MaxValue" in str(m):
                        data["metrics"]["vo2max"] = m.get("vo2MaxValue")
                        break
    except Exception as e:
        log.warning(f"Max metrics fetch failed: {e}")
    
    return data


def generate_report(data, user_prefs=None):
    """Generate a human-readable report from collected data."""
    
    if user_prefs is None:
        user_prefs = {}
    
    report = []
    report.append("# Garmin Connect Analysis Report")
    report.append("")
    report.append(f"**Generated:** {data['collection_date']}")
    report.append(f"**Period:** {data['period']['days']} days")
    report.append("")
    
    # Profile - no personal data (name, weight, etc.) for privacy
    report.append("## Profile")
    report.append("")
    p = data.get("profile", {})
    if p.get("gender"):
        report.append(f"- **Gender:** {p.get('gender')}")
    if p.get("birth_date"):
        birth = datetime.fromisoformat(p.get("birth_date").replace("Z", "+00:00"))
        age = (datetime.now() - birth.replace(tzinfo=None)).days // 365
        report.append(f"- **Age:** {age} years")
    
    # Get VO2 Max from metrics if available
    vo2max = data.get("metrics", {}).get("vo2max")
    if not vo2max and data.get("activities"):
        # Estimate from recent activities
        running = [a for a in data["activities"] if a.get("type") == "running" and a.get("vo2max")]
        if running:
            vo2max = running[0].get("vo2max")
    if vo2max:
        report.append(f"- **Estimated VO2 Max:** {vo2max}")
    report.append("")
    
    # User training preferences
    if user_prefs:
        report.append("## Training Goals & Preferences")
        report.append("")
        if user_prefs.get("GOAL_RACE"):
            report.append(f"- **Goal race:** {user_prefs.get('GOAL_RACE')}")
        if user_prefs.get("GOAL_DATE"):
            report.append(f"- **Goal date:** {user_prefs.get('GOAL_DATE')}")
        if user_prefs.get("TRAINING_DAYS"):
            report.append(f"- **Training days/week:** {user_prefs.get('TRAINING_DAYS')}")
        if user_prefs.get("MAX_SESSION_MINUTES"):
            report.append(f"- **Max session length:** {user_prefs.get('MAX_SESSION_MINUTES')} minutes")
        if user_prefs.get("INJURY_HISTORY"):
            report.append(f"- **Injury history:** {user_prefs.get('INJURY_HISTORY')}")
        if user_prefs.get("RACE_PACE_TARGET"):
            report.append(f"- **Target race pace:** {user_prefs.get('RACE_PACE_TARGET')}/km")
        if user_prefs.get("PREFERRED_TIME"):
            report.append(f"- **Preferred time:** {user_prefs.get('PREFERRED_TIME')}")
        if user_prefs.get("PREFERRED_LOCATION"):
            report.append(f"- **Training location:** {user_prefs.get('PREFERRED_LOCATION')}")
        
        # Pace targets
        report.append("")
        report.append("### Pace Targets (based on current fitness)")
        if user_prefs.get("EASY_PACE"):
            report.append(f"- **Easy runs:** {user_prefs.get('EASY_PACE')}/km")
        if user_prefs.get("TEMPO_PACE"):
            report.append(f"- **Tempo runs:** {user_prefs.get('TEMPO_PACE')}/km")
        if user_prefs.get("INTERVAL_PACE"):
            report.append(f"- **Interval/track:** {user_prefs.get('INTERVAL_PACE')}/km")
        if user_prefs.get("RACE_PACE_TARGET"):
            report.append(f"- **10K race pace:** {user_prefs.get('RACE_PACE_TARGET')}/km")
        
        report.append("")
    
    # Recent activities summary
    report.append("## Recent Activities (Last 90 Days)")
    report.append("")
    activities = data.get("activities", [])
    if activities:
        running = [a for a in activities if a.get("type") == "running"]
        report.append(f"- **Total activities:** {len(activities)}")
        report.append(f"- **Running activities:** {len(running)}")
        
        if running:
            total_dist = sum(a.get("distance_m", 0) for a in running) / 1000
            total_duration = sum(a.get("duration_sec", 0) for a in running) / 3600
            avg_hr = sum(a.get("avg_hr", 0) for a in running if a.get("avg_hr")) / max(1, len([a for a in running if a.get("avg_hr")]))
            
            report.append(f"- **Total distance:** {total_dist:.0f} km")
            report.append(f"- **Total time:** {total_duration:.0f} hours")
            report.append(f"- **Average HR:** {avg_hr:.0f} bpm")
            
            # Calculate weekly averages
            days = data["period"]["days"]
            weekly_runs = len(running) / (days / 7)
            weekly_dist = total_dist / (days / 7)
            weekly_time = total_duration / (days / 7)
            
            report.append(f"- **Weekly frequency:** {weekly_runs:.1f} runs/week")
            report.append(f"- **Weekly volume:** {weekly_dist:.0f} km")
            report.append(f"- **Weekly time:** {weekly_time:.1f} hours")
            
            # Recent activity (last 10)
            report.append("")
            report.append("### Recent Runs")
            report.append("")
            report.append("| Date | Activity | Duration | Distance | Avg HR |")
            report.append("|------|----------|----------|----------|--------|")
            for a in running[:10]:
                date = a.get("date", "")[:10] if a.get("date") else "N/A"
                name = a.get("name", "N/A")[:30]
                dur = a.get("duration_sec", 0) / 60
                dist = a.get("distance_m", 0) / 1000
                hr = a.get("avg_hr", 0) or 0
                report.append(f"| {date} | {name} | {dur:.0f} min | {dist:.1f} km | {hr:.0f} |")
    else:
        report.append("No activities found in this period.")
    report.append("")
    
    # Sleep summary
    report.append("## Sleep Analysis")
    report.append("")
    sleep = data.get("sleep", [])
    if sleep:
        valid_sleep = [s for s in sleep if s.get("duration_sec", 0) > 0]
        if valid_sleep:
            avg_duration = sum(s.get("duration_sec", 0) for s in valid_sleep) / len(valid_sleep) / 3600
            avg_deep = sum(s.get("deep_sec", 0) for s in valid_sleep) / len(valid_sleep) / 60
            avg_rem = sum(s.get("rem_sec", 0) for s in valid_sleep) / len(valid_sleep) / 60
            
            report.append(f"- **Nights tracked:** {len(valid_sleep)}")
            report.append(f"- **Avg duration:** {avg_duration:.1f} hours")
            report.append(f"- **Avg deep sleep:** {avg_deep:.0f} minutes")
            report.append(f"- **Avg REM sleep:** {avg_rem:.0f} minutes")
            
            # Recent sleep
            report.append("")
            report.append("### Recent Sleep")
            report.append("")
            report.append("| Date | Duration | Deep | REM | Quality |")
            report.append("|------|----------|------|-----|---------|")
            for s in valid_sleep[:7]:
                date = s.get("date", "N/A")
                dur = s.get("duration_sec", 0) / 3600
                deep = s.get("deep_sec", 0) / 60
                rem = s.get("rem_sec", 0) / 60
                quality = s.get("quality", "N/A")
                report.append(f"| {date} | {dur:.1f}h | {deep:.0f}m | {rem:.0f}m | {quality} |")
        else:
            report.append("No valid sleep records (off-wrist detected).")
    else:
        report.append("No sleep data found.")
    report.append("")
    
    # Race predictions
    report.append("## Race Predictions")
    report.append("")
    races = data.get("race_predictions", {})
    
    # Try Garmin predictions first, fall back to our local predictions
    has_garmin_predictions = races and any(races.get(k) for k in ['raceTime5K', 'raceTime10K', 'raceTimeHalf', 'raceTimeMarathon'])
    
    if has_garmin_predictions:
        report.append("### Garmin Predictions")
        report.append(f"- **5K:** {format_duration(races.get('raceTime5K', 0))}")
        report.append(f"- **10K:** {format_duration(races.get('raceTime10K', 0))}")
        report.append(f"- **Half Marathon:** {format_duration(races.get('raceTimeHalf', 0))}")
        report.append(f"- **Marathon:** {format_duration(races.get('raceTimeMarathon', 0))}")
    else:
        # Calculate our own predictions from activities
        activities = data.get("activities", [])
        running = [a for a in activities if a.get("type") == "running" and a.get("avg_pace")]
        
        if running:
            local_predictions = calculate_local_predictions(running)
            if local_predictions:
                report.append("### Calculated (Riegel formula)")
                for race, time_sec in local_predictions.items():
                    report.append(f"- **{race}:** {format_duration(time_sec)}")
        else:
            report.append("No race predictions available.")
    report.append("")
    
    # HRV
    report.append("## HRV (Heart Rate Variability)")
    report.append("")
    hrv = data.get("hrv", [])
    if hrv:
        latest = hrv[-1]
        avg_hrv = sum(h.get("avg_hrv", 0) for h in hrv if h.get("avg_hrv")) / max(1, len([h for h in hrv if h.get("avg_hrv")]))
        report.append(f"- **Latest HRV:** {latest.get('avg_hrv', 'N/A')} ms")
        report.append(f"- **7-day average:** {avg_hrv:.1f} ms")
        
        # Recent HRV
        report.append("")
        report.append("### Recent HRV")
        report.append("")
        report.append("| Date | Average | Min | Max |")
        report.append("|------|---------|-----|-----|")
        for h in hrv[-7:]:
            date = h.get("date", "N/A")
            avg = h.get("avg_hrv", 0) or 0
            min_h = h.get("min_hrv", 0) or 0
            max_h = h.get("max_hrv", 0) or 0
            report.append(f"| {date} | {avg} ms | {min_h} ms | {max_h} ms |")
    else:
        report.append("No HRV data available.")
    report.append("")
    
    # Training readiness
    report.append("## Training Readiness")
    report.append("")
    readiness = data.get("training_readiness", [])
    if readiness:
        latest = readiness[-1]
        report.append(f"- **Latest:** {latest.get('value', 'N/A')} ({latest.get('status', 'N/A')})")
        
        # Trend
        values = [r.get("value", 0) for r in readiness if r.get("value")]
        if values:
            avg = sum(values) / len(values)
            report.append(f"- **7-day average:** {avg:.0f}")
            
            # Recent readings
            report.append("")
            report.append("### Recent Readiness")
            report.append("")
            report.append("| Date | Value | Status |")
            report.append("|------|-------|--------|")
            for r in readiness[-7:]:
                date = r.get("date", "N/A")
                val = r.get("value", "N/A")
                status = r.get("status", "N/A")
                report.append(f"| {date} | {val} | {status} |")
    else:
        report.append("No training readiness data available.")
    report.append("")
    
    # Training status
    report.append("## Training Status")
    report.append("")
    training_status = data.get("metrics", {}).get("training_status")
    if training_status:
        if isinstance(training_status, dict):
            report.append(f"- **Status:** {training_status.get('trainingStatusLabel', 'N/A')}")
            report.append(f"- **Load:** {training_status.get('currentDayAcuteLoad', 'N/A')}")
        else:
            report.append(str(training_status)[:500])
    else:
        report.append("No training status data available.")
    report.append("")
    
    # Summary for LLM
    report.append("## Summary for Training Plan Generation")
    report.append("")
    
    # Calculate training stats
    if activities:
        running = [a for a in activities if a.get("type") == "running"]
        if running:
            weekly_runs = len(running) / (data['period']['days'] / 7)
            weekly_dist = sum(a.get("distance_m", 0) for a in running) / 1000 / (data['period']['days'] / 7)
            weekly_time = sum(a.get("duration_sec", 0) for a in running) / 3600 / (data['period']['days'] / 7)
            
            report.append(f"- **Weekly frequency:** {weekly_runs:.1f} runs/week")
            report.append(f"- **Weekly volume:** {weekly_dist:.0f} km")
            report.append(f"- **Weekly time:** {weekly_time:.1f} hours")
            report.append(f"- **Total activities:** {len(activities)} in {data['period']['days']} days")
            
            # Recent intensity
            recent = running[:5]
            avg_intensity = sum(a.get("avg_hr", 0) for a in recent if a.get("avg_hr")) / max(1, len([a for a in recent if a.get("avg_hr")]))
            report.append(f"- **Recent avg HR:** {avg_intensity:.0f} bpm")
    
    # VO2 Max estimate
    if vo2max:
        report.append(f"- **Current fitness level:** VO2 Max {vo2max}")
    elif data["activities"]:
        running = [a for a in data["activities"] if a.get("type") == "running" and a.get("vo2max")]
        if running:
            report.append(f"- **Current fitness level:** VO2 Max {running[0].get('vo2max')}")
    
    # Sleep quality
    if sleep:
        valid_sleep = [s for s in sleep if s.get("duration_sec", 0) > 0]
        if valid_sleep:
            avg_duration = sum(s.get("duration_sec", 0) for s in valid_sleep) / len(valid_sleep) / 3600
            report.append(f"- **Sleep quality:** {avg_duration:.1f} hours/night average")
    
    # HRV
    if hrv:
        avg_hrv = sum(h.get("avg_hrv", 0) for h in hrv if h.get("avg_hrv")) / max(1, len([h for h in hrv if h.get("avg_hrv")]))
        report.append(f"- **HRV status:** {avg_hrv:.0f} ms average")
    
    # Training readiness summary
    if readiness:
        values = [r.get("value", 0) for r in readiness if r.get("value")]
        if values:
            avg = sum(values) / len(values)
            report.append(f"- **Training readiness:** {avg:.0f} average")
    
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Instructions for Training Plan Generation")
    report.append("")
    report.append("When creating a training plan, read these files for scientific guidance:")
    report.append("")
    report.append("1. **TRAINING_GUIDELINES.md** - Training principles and workout structure")
    report.append("2. **RESEARCH_TRAINING_PRINCIPLES.md** - Scientific backing for 80/20 polarized training")
    report.append("")
    report.append("**Plan Requirements:**")
    report.append("- Use 80/20 polarized training (80% easy, 20% hard)")
    report.append("- Include deload weeks every 3-4 weeks")
    report.append("- Progressive overload with realistic pace targets")
    report.append("- Build volume gradually, peak 2-3 weeks before race")
    report.append("- Taper last 1-2 weeks before race")
    report.append("")
    report.append("---")
    report.append("*Report generated by Garmin Analyzer*")
    
    return "\n".join(report)


def main():
    log.info("Garmin Connect Data Collector")
    log.info("=" * 40)
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    log.info("Connecting to Garmin Connect...")
    try:
        client = get_client()
        log.info("Connected!")
    except Exception as e:
        log.error(f"Failed to connect: {e}")
        log.info("Run garmin_auth_browser.py first to authenticate.")
        return
    
    log.info("")
    data = collect_all_data(client, days=90)
    
    user_prefs = load_user_preferences()
    if user_prefs:
        log.info(f"Loaded preferences: {list(user_prefs.keys())}")
    
    log.info("Saving data...")
    with open(REPORT_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    log.info(f"Raw data: {REPORT_FILE}")
    
    report = generate_report(data, user_prefs)
    report_file = OUTPUT_DIR / "garmin_report.md"
    with open(report_file, 'w') as f:
        f.write(report)
    log.info(f"Report: {report_file}")
    
    log.info("=" * 40)
    log.info("Done!")
    log.info(f"Open {report_file} to see the analysis.")
    log.info("Share this report with an LLM to generate a training plan.")


if __name__ == "__main__":
    main()
