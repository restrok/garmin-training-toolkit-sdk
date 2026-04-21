import logging
from typing import List
from ..models.activities import Activity, ActivitySplit

log = logging.getLogger(__name__)

def get_activity_splits(client, activity_id: int) -> List[ActivitySplit]:
    """Fetch detailed splits for an activity."""
    try:
        splits_data = client.get_activity_splits(activity_id)
        if splits_data and "lapDTOs" in splits_data:
            laps = []
            for lap in splits_data["lapDTOs"]:
                laps.append(ActivitySplit(
                    index=lap.get("lapIndex"),
                    type=lap.get("intensityType"),
                    distance_m=lap.get("distance"),
                    duration_sec=lap.get("duration"),
                    moving_duration_sec=lap.get("movingDuration"),
                    avg_hr=lap.get("averageHR"),
                    max_hr=lap.get("maxHR"),
                    avg_pace_mps=lap.get("averageMovingSpeed"),
                    avg_cadence=lap.get("averageRunCadence"),
                    calories=lap.get("calories")
                ))
            return laps
    except Exception as e:
        log.warning(f"Failed to get splits for {activity_id}: {e}")
    return []

def get_activities(client, start_date: str, end_date: str) -> List[Activity]:
    """Fetch activities within a date range."""
    activities = []
    try:
        raw_activities = client.get_activities_by_date(start_date, end_date)
        for a in raw_activities:
            activity_date = a.get("startTimeLocal", "")
            
            activity = Activity(
                id=a.get("activityId"),
                name=a.get("activityName", "Unknown"),
                type=a.get("activityType", {}).get("typeKey", "unknown"),
                date=activity_date,
                duration_sec=a.get("duration"),
                distance_m=a.get("distance"),
                avg_hr=a.get("averageHR"),
                max_hr=a.get("maxHR"),
                avg_pace=a.get("averageSpeed"),
                calories=a.get("calories"),
                elevation_gain=a.get("elevationGain"),
                vo2max=a.get("vO2MaxValue")
            )
            # You might want to fetch splits lazily or keep this separate to avoid rate limits
            activities.append(activity)
    except Exception as e:
        log.warning(f"Activities fetch failed: {e}")
    return activities
