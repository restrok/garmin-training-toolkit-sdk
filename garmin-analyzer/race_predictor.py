#!/usr/bin/env python3
"""
Race Predictor
Predicts race finish times based on current fitness (VO2max, recent training data).
"""

import logging
import math
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
log = logging.getLogger(__name__)


def calculate_vdot(vo2max: float, race_pace_sec: int) -> float:
    """Calculate VDOT from VO2max and race pace."""
    return vo2max


def predict_race_time(vo2max: float, race_type: str, pace_factor: float = 0.85) -> dict:
    """
    Predict race time using VDOT formula.
    Uses Jack Daniels' VDOT formula approximations.
    """
    if not vo2max:
        return {"error": "No VO2max data"}
    
    # Race distances in km
    race_distances = {
        "5K": 5.0,
        "10K": 10.0,
        "half": 21.0975,
        "marathon": 42.195,
    }
    
    # Percentage of VO2max at different race distances
    intensity = {
        "5K": 0.95,
        "10K": 0.90,
        "half": 0.85,
        "marathon": 0.80,
    }
    
    if race_type not in race_distances:
        return {"error": f"Unknown race type: {race_type}"}
    
    dist = race_distances[race_type]
    pct = intensity[race_type]
    
    # Calculate predicted time in seconds
    # Using simplified VDOT formula: VO2 = (velocity * 0.2 + 0.2) * percentage adjustment
    # This is an approximation of the Daniels formula
    
    # Convert pace (sec/km) to velocity (m/min)
    # Using percentage of max effort
    effort_pace_sec = (300 / vo2max) * 100 * pct
    
    # Adjust for race distance (longer = slower per km due to fatigue)
    fatigue_factor = 1.0 + (dist / 100) * 0.05
    
    predicted_pace_sec = effort_pace_sec * fatigue_factor
    total_seconds = predicted_pace_sec * dist
    
    hours = int(total_seconds) // 3600
    mins = (int(total_seconds) % 3600) // 60
    secs = int(total_seconds) % 60
    
    # Format pace per km
    pace_mins = int(predicted_pace_sec) // 60
    pace_sec = int(predicted_pace_sec) % 60
    
    return {
        "race": race_type,
        "distance_km": dist,
        "predicted_time_sec": int(total_seconds),
        "formatted_time": f"{hours}:{mins:02d}:{secs:02d}",
        "predicted_pace": f"{pace_mins}:{pace_sec:02d}/km",
        "vo2max": vo2max,
    }


def predict_from_recent_performance(activities: list[dict]) -> dict:
    """Predict race times based on recent training data."""
    running = [a for a in activities if a.get("type") == "running"]
    
    if not running:
        return {"error": "No running activities found"}
    
    # Get recent easy run pace as baseline
    recent_easy = []
    for a in running[:10]:
        pace = a.get("avg_pace")
        if pace and pace > 0:
            # pace is in m/s, convert to sec/km
            sec_per_km = 1000 / pace
            recent_easy.append({
                "date": a.get("date", ""),
                "distance_km": a.get("distance_m", 0) / 1000,
                "pace_sec_km": sec_per_km,
                "hr": a.get("avg_hr"),
            })
    
    if not recent_easy:
        return {"error": "No pace data found"}
    
    avg_easy_pace = sum(e["pace_sec_km"] for e in recent_easy) / len(recent_easy)
    
    # Estimate VO2max from easy pace (approximation)
    # At easy pace (roughly 65% max HR), VO2 is about 60-70% of max
    # Using 68% as average
    estimated_vo2max = (300 / avg_easy_pace) * 100 / 0.68
    
    # Predict all race times
    predictions = {}
    for race in ["5K", "10K", "half", "marathon"]:
        result = predict_race_time(estimated_vo2max, race)
        if "error" not in result:
            predictions[race] = result
    
    return {
        "estimated_vo2max": round(estimated_vo2max, 1),
        "avg_easy_pace": f"{int(avg_easy_pace)//60}:{int(avg_easy_pace)%60:02d}/km",
        "predictions": predictions,
    }


def get_garmin_predictions(client) -> dict:
    """Get official Garmin race predictions."""
    try:
        races = client.get_race_predictions()
        if races:
            if isinstance(races, list):
                races = races[-1]
            return {
                "5K": races.get("raceTime5K"),
                "10K": races.get("raceTime10K"),
                "half": races.get("raceTimeHalf"),
                "marathon": races.get("raceTimeMarathon"),
            }
    except Exception as e:
        log.warning(f"Could not fetch Garmin predictions: {e}")
    return {}


def format_time(seconds: int) -> str:
    """Format seconds to H:MM:SS."""
    if not seconds:
        return "N/A"
    hours = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    if hours:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


def print_predictions(predictions: dict):
    """Print race predictions."""
    print("\n" + "=" * 50)
    print("RACE PREDICTIONS")
    print("=" * 50)
    
    if "estimated_vo2max" in predictions:
        print(f"\n📊 Estimated VO2max: {predictions['estimated_vo2max']}")
        print(f"   Avg Easy Pace: {predictions['avg_easy_pace']}")
    
    if "predictions" in predictions:
        print("\n🏃 Predicted Finish Times")
        for race, p in predictions["predictions"].items():
            print(f"  {race:10s}: {p['formatted_time']} ({p['predicted_pace']}/km)")
    
    print("\n" + "=" * 50)


def main():
    import argparse
    import sys
    import json
    from pathlib import Path
    
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from garmin_utils import find_token_file, get_authenticated_client, load_env_file
    from garmin_analyzer.database import get_activities_since
    
    parser = argparse.ArgumentParser(description="Race Predictor")
    parser.add_argument("--race", choices=["5K", "10K", "half", "marathon"], help="Specific race")
    parser.add_argument("--garmin", action="store_true", help="Use Garmin official predictions")
    parser.add_argument("--days", type=int, default=30, help="Days to analyze for performance")
    args = parser.parse_args()
    
    log.info("Race Predictor")
    
    # Load from database or generate
    activities = get_activities_since((datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d"))
    
    predictions = predict_from_recent_performance(activities)
    
    if args.garmin:
        token_file = find_token_file()
        if token_file:
            client = get_authenticated_client(token_file)
            try:
                client.login()
                garmin_preds = get_garmin_predictions(client)
                if garmin_preds:
                    print("\n📱 Garmin Official Predictions")
                    for race, time_sec in garmin_preds.items():
                        if time_sec:
                            print(f"  {race:10s}: {format_time(time_sec)}")
            except Exception as e:
                log.warning(f"Garmin login failed: {e}")
    
    if args.race:
        pred = predictions.get("predictions", {}).get(args.race)
        if pred:
            print(f"\n{args.race} Prediction: {pred['formatted_time']} ({pred['predicted_pace']}/km)")
        else:
            print(f"\nNo prediction for {args.race}")
    else:
        print_predictions(predictions)


if __name__ == "__main__":
    main()
