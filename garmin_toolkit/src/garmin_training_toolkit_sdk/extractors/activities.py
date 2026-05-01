import logging
from typing import List
from ..protocol.activities import Activity, ActivitySplit
from ..protocol.telemetry import ActivityTelemetry, ActivityTelemetryPoint

log = logging.getLogger(__name__)

def get_activity_telemetry(client, activity_id: int) -> ActivityTelemetry:
    """Fetch second-by-second telemetry data for an activity."""
    try:
        details = client.get_activity_details(activity_id)
        if not details or "activityDetailMetrics" not in details:
            return ActivityTelemetry(activity_id=activity_id, metric_count=0, ticks=[])
        
        descriptors = details.get("metricDescriptors", [])
        raw_metrics = details.get("activityDetailMetrics", [])
        
        # Create a mapping of metric key to its array index
        key_to_index = {d["key"]: d["metricsIndex"] for d in descriptors}
        
        # Helper to safely extract a value from the metrics array
        def get_val(metric_array, key):
            if key in key_to_index:
                idx = key_to_index[key]
                if idx < len(metric_array):
                    return metric_array[idx]
            return None

        ticks = []
        for tick_data in raw_metrics:
            metrics_array = tick_data.get("metrics", [])
            if not metrics_array:
                continue
                
            # Time must exist
            timestamp = get_val(metrics_array, "directTimestamp")
            if timestamp is None:
                continue
                
            ticks.append(ActivityTelemetryPoint(
                timestamp_ms=int(timestamp),
                lat=get_val(metrics_array, "directLatitude"),
                lng=get_val(metrics_array, "directLongitude"),
                elevation_m=get_val(metrics_array, "directElevation"),
                speed_mps=get_val(metrics_array, "directSpeed"),
                hr_bpm=get_val(metrics_array, "directHeartRate"),
                cadence_spm=get_val(metrics_array, "directDoubleCadence"),
                power_w=get_val(metrics_array, "directPower"),
                fractional_cadence=get_val(metrics_array, "directFractionalCadence"),
                gap_mps=get_val(metrics_array, "directGradeAdjustedSpeed"),
                stride_length_mm=get_val(metrics_array, "directStrideLength"),
                vertical_oscillation_cm=get_val(metrics_array, "directVerticalOscillation"),
                ground_contact_time_ms=get_val(metrics_array, "directGroundContactTime"),
                temperature_c=get_val(metrics_array, "directAmbientTemperature") if get_val(metrics_array, "directAmbientTemperature") is not None else get_val(metrics_array, "directAirTemperature"),
                run_walk_index=get_val(metrics_array, "directRunWalkIndex")
            ))
            
        return ActivityTelemetry(
            activity_id=activity_id,
            metric_count=len(ticks),
            ticks=ticks
        )
    except Exception as e:
        log.error(f"Failed to fetch telemetry for {activity_id}: {e}")
        return ActivityTelemetry(activity_id=activity_id, metric_count=0, ticks=[])

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
                    calories=lap.get("calories"),
                    strokes=lap.get("strokes"),
                    avg_swolf=lap.get("averageSWOLF")
                ))
            return laps
    except Exception as e:
        log.warning(f"Failed to get splits for {activity_id}: {e}")
    return []

def get_activities(client, start_date: str, end_date: str, limit: int = 20) -> List[Activity]:
    """Fetch activities within a date range."""
    activities = []
    try:
        # Note: Garmin API usually uses start and limit for this endpoint
        # if using get_activities. If using by date, we might need a different client method.
        # For now, let's keep it consistent with how it's being called.
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
                vo2max=a.get("vO2MaxValue"),
                pool_length_m=a.get("poolLength"),
                total_strokes=a.get("strokes"),
                avg_swolf=a.get("averageSWOLF")
            )
            # You might want to fetch splits lazily or keep this separate to avoid rate limits
            activities.append(activity)
    except Exception as e:
        log.warning(f"Activities fetch failed: {e}")
    return activities
