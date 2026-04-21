import logging
from typing import List
from ..models.biometrics import HRVData, SleepData, ReadinessData

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
