import logging
from typing import List, Optional
from ..models.biometrics import HRVData, SleepData, ReadinessData, BodyBatteryData, StressData, TrainingStatusData

log = logging.getLogger(__name__)

def get_hrv_data(client, start_date: str, end_date: str) -> List[HRVData]:
    """Fetch HRV data for a given date range."""
    hrv_records = []
    try:
        # Garmin API typically fetches end date or recent.
        raw_hrv = client.get_hrv_data(end_date)
        if raw_hrv and isinstance(raw_hrv, list):
            for h in raw_hrv:
                date = h.get("calendarDate")
                if start_date <= date <= end_date:
                    hrv_records.append(HRVData(
                        date=date,
                        avg_hrv=h.get("averageHRV"),
                        min_hrv=h.get("minHRV"),
                        max_hrv=h.get("maxHRV")
                    ))
    except Exception as e:
        log.warning(f"HRV data fetch failed: {e}")
    return hrv_records

def get_sleep_data(client, start_date: str, end_date: str) -> List[SleepData]:
    sleep_records = []
    try:
        raw_sleep = client.get_sleep_data(start_date, end_date)
        if raw_sleep:
            for s in raw_sleep:
                sleep_records.append(SleepData(
                    date=s.get("calendarDate", ""),
                    start=s.get("sleepStartTimestampGMT"),
                    end=s.get("sleepEndTimestampGMT"),
                    duration_sec=s.get("sleepTimeSeconds"),
                    deep_sec=s.get("deepSleepSeconds"),
                    light_sec=s.get("lightSleepSeconds"),
                    rem_sec=s.get("remSleepSeconds"),
                    awake_sec=s.get("awakeSleepSeconds"),
                    quality=s.get("sleepWindowConfirmationType")
                ))
    except Exception as e:
        log.warning(f"Sleep data fetch failed: {e}")
    return sleep_records

def get_readiness_data(client, date: str) -> List[ReadinessData]:
    readiness_records = []
    try:
        raw_readiness = client.get_morning_training_readiness(date)
        if raw_readiness and isinstance(raw_readiness, list):
            for r in raw_readiness:
                readiness_records.append(ReadinessData(
                    date=r.get("calendarDate", ""),
                    value=r.get("trainingReadinessValue"),
                    status=r.get("trainingReadinessStatus")
                ))
    except Exception as e:
        log.warning(f"Training readiness fetch failed: {e}")
    return readiness_records

def get_body_battery(client, date: str) -> Optional[BodyBatteryData]:
    """Fetch body battery data for a specific date."""
    try:
        raw_bb = client.get_body_battery(date)
        if raw_bb:
            # Usually it returns a list of items for the day, with a daily summary.
            # Depending on Garmin's payload, it might look like {"charged": X, "drained": Y}
            # We will extract the high level info. The actual timeline data is usually in 'bodyBatteryValuesArray'
            
            # The structure returned by garminconnect is typically a list with a single dict
            if isinstance(raw_bb, list) and len(raw_bb) > 0:
                data = raw_bb[0]
                values = data.get("bodyBatteryValuesArray", [])
                return BodyBatteryData(
                    date=data.get("date", date),
                    charged=data.get("charged"),
                    drained=data.get("drained"),
                    highest=data.get("highest"),
                    lowest=data.get("lowest"),
                    values_count=len(values)
                )
    except Exception as e:
        log.warning(f"Body battery fetch failed for {date}: {e}")
    return None

def get_stress_data(client, date: str) -> Optional[StressData]:
    """Fetch stress data for a specific date."""
    try:
        raw_stress = client.get_stress_data(date)
        if raw_stress:
            return StressData(
                date=raw_stress.get("calendarDate", date),
                max_stress_level=raw_stress.get("maxStressLevel"),
                avg_stress_level=raw_stress.get("avgStressLevel"),
                stress_duration_sec=raw_stress.get("stressDuration"),
                rest_duration_sec=raw_stress.get("restStressDuration"),
                activity_duration_sec=raw_stress.get("activityStressDuration"),
                low_stress_duration_sec=raw_stress.get("lowStressDuration"),
                medium_stress_duration_sec=raw_stress.get("mediumStressDuration"),
                high_stress_duration_sec=raw_stress.get("highStressDuration")
            )
    except Exception as e:
        log.warning(f"Stress data fetch failed for {date}: {e}")
    return None

def get_training_status(client, date: str) -> Optional[TrainingStatusData]:
    """Fetch training status for a specific date."""
    try:
        raw_status = client.get_training_status(date)
        if raw_status:
            return TrainingStatusData(
                date=date,
                status=raw_status.get("trainingStatusLabel"),
                acute_load=raw_status.get("currentDayAcuteLoad"),
                chronic_load=raw_status.get("currentDayChronicLoad"),
                load_focus=raw_status.get("loadFocus"),
                vo2max=raw_status.get("vo2MaxValue")
            )
    except Exception as e:
        log.warning(f"Training status fetch failed for {date}: {e}")
    return None
