import logging
from datetime import datetime, timedelta
from typing import Any, List, Optional, Tuple

from garminconnect import Garmin, GarminConnectConnectionError

from ..protocol.biometrics import (
    BodyBatteryData,
    HRVData,
    ReadinessData,
    RespirationData,
    SleepData,
    StressData,
    TrainingStatusData,
)
from ..protocol.user import BodyComposition, UserProfile

log = logging.getLogger(__name__)


def get_user_profile(garmin_client: Garmin) -> Optional[UserProfile]:
    """Fetch user profile information by combining data from multiple endpoints.

    Args:
        garmin_client: The Garmin API client instance.

    Returns:
        A UserProfile object if successful, None otherwise.
    """
    try:
        profile = garmin_client.get_user_profile()
        settings = garmin_client.get_userprofile_settings()

        user_data = profile.get("userData", {})

        # Calculate age from birthDate
        age = None
        birth_date_str = user_data.get("birthDate")
        if birth_date_str:
            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
            today = datetime.now()
            age = (
                today.year
                - birth_date.year
                - ((today.month, today.day) < (birth_date.month, birth_date.day))
            )

        # Weight is in grams in userData
        weight_kg = user_data.get("weight")
        if weight_kg:
            weight_kg = weight_kg / 1000.0

        return UserProfile(
            display_name=settings.get("displayName"),
            gender=user_data.get("gender"),
            age=age,
            height_cm=user_data.get("height"),
            weight_kg=weight_kg,
            max_hr=user_data.get("maxHeartRate"),
            resting_hr=user_data.get("restingHeartRate"),
        )
    except Exception as e:
        log.warning("User profile fetch failed: %s", e)
    return None


def get_body_composition(
    garmin_client: Garmin, start_date: str, end_date: str
) -> List[BodyComposition]:
    """Fetch body composition data for a date range.

    Args:
        garmin_client: The Garmin API client instance.
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).

    Returns:
        A list of BodyComposition records.
    """
    composition_records = []
    try:
        raw_composition = garmin_client.get_body_composition(start_date, end_date)
        if raw_composition and "allMetrics" in raw_composition:
            for m in raw_composition["allMetrics"]:
                composition_records.append(
                    BodyComposition(
                        date=m.get("calendarDate"),
                        weight_kg=m.get("weight"),
                        bmi=m.get("bmi"),
                        fat_percentage=m.get("bodyFat"),
                        muscle_mass_kg=m.get("muscleMass"),
                        water_percentage=m.get("waterPercentage"),
                    )
                )
    except Exception as e:
        log.warning("Body composition fetch failed: %s", e)
    return composition_records


def get_hrv_data(
    garmin_client: Garmin, start_date: str, end_date: str
) -> List[HRVData]:
    """Fetch HRV data for a given date range by iterating through each day.

    Args:
        garmin_client: The Garmin API client instance.
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).

    Returns:
        A list of HRVData records.
    """
    hrv_records = []

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    current = start

    while current <= end:
        curr_str = current.strftime("%Y-%m-%d")
        try:
            # Underlying client method only takes a single date string
            raw = garmin_client.get_hrv_data(curr_str)

            if raw and "hrvSummary" in raw:
                summary = raw["hrvSummary"]
                date = summary.get("calendarDate")
                if date == curr_str:
                    baseline = summary.get("baseline", {})
                    hrv_records.append(
                        HRVData(
                            date=date,
                            last_night_avg=summary.get("lastNightAvg"),
                            min_hrv=None,
                            max_hrv=summary.get("lastNight5MinHigh"),
                            status=summary.get("status"),
                            baseline_low=baseline.get("balancedLow"),
                            baseline_high=baseline.get("balancedUpper"),
                        )
                    )
            elif isinstance(raw, list):
                # Fallback for different API versions or multi-day responses
                for h in raw:
                    date = h.get("calendarDate")
                    if date == curr_str:
                        baseline = h.get("baseline", {})
                        hrv_records.append(
                            HRVData(
                                date=date,
                                last_night_avg=h.get("averageHRV")
                                or h.get("lastNightAvg"),
                                min_hrv=h.get("minHRV"),
                                max_hrv=h.get("maxHRV") or h.get("lastNight5MinHigh"),
                                status=h.get("status"),
                                baseline_low=baseline.get("balancedLow"),
                                baseline_high=baseline.get("balancedUpper"),
                            )
                        )
        except (GarminConnectConnectionError, Exception) as e:
            error_msg = str(e).lower()
            if "404" in error_msg or "400" in error_msg:
                log.info(
                    "HRV endpoint 404/400 for %s. Attempting sleep fallback...",
                    curr_str,
                )
                try:
                    # Fallback Strategy: Extract from Sleep Payload
                    sleep_data = garmin_client.get_sleep_data(cdate=curr_str)
                    if isinstance(sleep_data, dict):
                        fallback_avg_hrv = sleep_data.get("avgOvernightHrv")
                        status = sleep_data.get("hrvStatus")
                        if fallback_avg_hrv is not None:
                            log.info(
                                "Successfully extracted HRV fallback from sleep data"
                            )
                            hrv_records.append(
                                HRVData(
                                    date=curr_str,
                                    last_night_avg=float(fallback_avg_hrv),
                                    status=status,
                                )
                            )
                            current += timedelta(days=1)
                            continue
                except Exception as sleep_err:
                    log.debug("Sleep fallback failed for %s: %s", curr_str, sleep_err)

            log.debug("HRV data for %s not available: %s", curr_str, e)
        current += timedelta(days=1)

    return hrv_records


def get_sleep_data(
    garmin_client: Garmin, start_date: str, end_date: str
) -> List[SleepData]:
    """Fetch sleep data by iterating through the date range.

    Args:
        garmin_client: The Garmin API client instance.
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).

    Returns:
        A list of SleepData records.
    """
    sleep_records = []
    try:
        curr = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        while curr <= end:
            date_str = curr.strftime("%Y-%m-%d")
            try:
                # Use keyword argument for stability
                s = garmin_client.get_sleep_data(cdate=date_str)
                dto = None
                if isinstance(s, dict):
                    if s.get("dailySleepDTO"):
                        dto = s["dailySleepDTO"]
                    elif "sleepTimeSeconds" in s:
                        dto = s

                if dto:
                    log.info("Found sleep record for %s", date_str)

                    sleep_scores = dto.get("sleepScores", {})
                    overall_score = sleep_scores.get("overall", {}).get("value")

                    def to_int(val: Any) -> Optional[int]:
                        if val is None:
                            return None
                        try:
                            return int(val)
                        except (ValueError, TypeError):
                            return None

                            # Extract restless moments

                    restless_moments = to_int(
                        dto.get("restlessMomentsCount")
                        if dto.get("restlessMomentsCount") is not None
                        else (
                            s.get("restlessMomentsCount")
                            if isinstance(s, dict)
                            else None
                        )
                    )

                    # Extract body battery change during sleep
                    body_battery_change = to_int(
                        dto.get("bodyBatteryChange")
                        if dto.get("bodyBatteryChange") is not None
                        else (
                            s.get("bodyBatteryChange") if isinstance(s, dict) else None
                        )
                    )

                    # Extract average overnight HRV
                    avg_overnight_hrv = None
                    raw_avg_hrv = (
                        s.get("avgOvernightHrv")
                        if isinstance(s, dict) and s.get("avgOvernightHrv") is not None
                        else dto.get("avgOvernightHrv")
                    )
                    if raw_avg_hrv is not None:
                        try:
                            avg_overnight_hrv = float(raw_avg_hrv)
                        except (ValueError, TypeError):
                            avg_overnight_hrv = None

                    # Extract 5-minute raw HRV readings [(timestamp_ms, hrv_value)]
                    hrv_readings_list: List[Tuple[int, float]] = []
                    raw_readings = (
                        s.get("hrvReadings")
                        if isinstance(s, dict)
                        and isinstance(s.get("hrvReadings"), list)
                        else dto.get("hrvReadings", [])
                    )
                    if isinstance(raw_readings, list):
                        for reading in raw_readings:
                            if isinstance(reading, dict):
                                hrv_val = reading.get("hrvValue")
                                ts_val = (
                                    reading.get("readingTimeGmt")
                                    or reading.get("timestampMs")
                                    or reading.get("readingTimeLocal")
                                )
                                if hrv_val is not None and ts_val is not None:
                                    try:
                                        if isinstance(ts_val, (int, float)):
                                            ts_epoch = int(ts_val)
                                        else:
                                            iso_str = str(ts_val).replace("Z", "")
                                            if "." in iso_str:
                                                head, tail = iso_str.split(".", 1)
                                                tail_digits = "".join([c for c in tail if c.isdigit()])
                                                tail_norm = (tail_digits + "000000")[:6]
                                                iso_str = f"{head}.{tail_norm}"
                                            ts_dt = datetime.fromisoformat(iso_str)
                                            ts_epoch = int(ts_dt.timestamp() * 1000)
                                        hrv_readings_list.append(
                                            (ts_epoch, float(hrv_val))
                                        )
                                    except Exception:
                                        pass

                    sleep_records.append(
                        SleepData(
                            date=dto.get("calendarDate", date_str),
                            start=to_int(dto.get("sleepStartTimestampGMT")),
                            end=to_int(dto.get("sleepEndTimestampGMT")),
                            duration_sec=to_int(dto.get("sleepTimeSeconds")),
                            deep_sec=to_int(dto.get("deepSleepSeconds")),
                            light_sec=to_int(dto.get("lightSleepSeconds")),
                            rem_sec=to_int(dto.get("remSleepSeconds")),
                            awake_sec=to_int(dto.get("awakeSleepSeconds")),
                            quality=to_int(overall_score),
                            restless_moments=restless_moments,
                            body_battery_change=body_battery_change,
                            avg_overnight_hrv=avg_overnight_hrv,
                            hrv_readings=hrv_readings_list,
                        )
                    )
            except Exception as e:
                log.debug("Sleep data for %s not available: %s", date_str, e)

            curr += timedelta(days=1)
    except Exception as e:
        log.warning("Error in sleep loop: %s", e)

    return sleep_records


def get_readiness_data(garmin_client: Garmin, date: str) -> List[ReadinessData]:
    """Fetch morning training readiness data.

    Args:
        garmin_client: The Garmin API client instance.
        date: Date string (YYYY-MM-DD).

    Returns:
        A list of ReadinessData records.
    """
    readiness_records = []
    try:
        raw_readiness = garmin_client.get_morning_training_readiness(date)
        if raw_readiness and isinstance(raw_readiness, list):
            for r in raw_readiness:
                readiness_records.append(
                    ReadinessData(
                        date=r.get("calendarDate", ""),
                        value=r.get("trainingReadinessValue"),
                        status=r.get("trainingReadinessStatus"),
                    )
                )
    except Exception as e:
        log.warning("Training readiness fetch failed: %s", e)
    return readiness_records


def get_body_battery(garmin_client: Garmin, date: str) -> Optional[BodyBatteryData]:
    """Fetch body battery data for a specific date.

    Args:
        garmin_client: The Garmin API client instance.
        date: Date string (YYYY-MM-DD).

    Returns:
        A BodyBatteryData object if successful, None otherwise.
    """
    try:
        raw_bb = garmin_client.get_body_battery(date)
        if raw_bb:
            if isinstance(raw_bb, list) and len(raw_bb) > 0:
                data = raw_bb[0]
                values = data.get("bodyBatteryValuesArray", [])
                return BodyBatteryData(
                    date=data.get("date", date),
                    charged=data.get("charged"),
                    drained=data.get("drained"),
                    highest=data.get("highest"),
                    lowest=data.get("lowest"),
                    values_count=len(values),
                )
    except Exception as e:
        log.warning("Body battery fetch failed for %s: %s", date, e)
    return None


def get_stress_data(garmin_client: Garmin, date: str) -> Optional[StressData]:
    """Fetch stress data for a specific date.

    Args:
        garmin_client: The Garmin API client instance.
        date: Date string (YYYY-MM-DD).

    Returns:
        A StressData object if successful, None otherwise.
    """
    try:
        raw_stress = garmin_client.get_stress_data(date)
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
                high_stress_duration_sec=raw_stress.get("highStressDuration"),
            )
    except Exception as e:
        log.warning("Stress data fetch failed for %s: %s", date, e)
    return None


def get_training_status(
    garmin_client: Garmin, date: str
) -> Optional[TrainingStatusData]:
    """Fetch training status for a specific date.

    Args:
        garmin_client: The Garmin API client instance.
        date: Date string (YYYY-MM-DD).

    Returns:
        A TrainingStatusData object if successful, None otherwise.
    """
    try:
        raw_status = garmin_client.get_training_status(date)
        if raw_status:
            return TrainingStatusData(
                date=date,
                status=raw_status.get("trainingStatusLabel"),
                acute_load=raw_status.get("currentDayAcuteLoad"),
                chronic_load=raw_status.get("currentDayChronicLoad"),
                load_focus=raw_status.get("loadFocus"),
                vo2max=raw_status.get("vo2MaxValue"),
            )
    except Exception as e:
        log.warning("Training status fetch failed for %s: %s", date, e)
    return None


def get_respiration_data(
    garmin_client: Garmin, date_str: str
) -> Optional[RespirationData]:
    """Fetch respiration data for a specific date.

    Args:
        garmin_client: The Garmin API client instance.
        date_str: Date string (YYYY-MM-DD).

    Returns:
        A RespirationData object if successful, None otherwise.
    """
    try:
        raw = garmin_client.get_respiration_data(date_str)
        if raw:
            cdate = datetime.strptime(date_str, "%Y-%m-%d").date()
            timeseries = []
            for val in raw.get("respirationValuesArray", []):
                if isinstance(val, list) and len(val) >= 2 and val[1] is not None:
                    timeseries.append((int(val[0]), float(val[1])))

            hourly_averages = []
            for val in raw.get("hourlyAverages", []):
                # Typically [timestamp, avg_resp, awake_resp, sleep_resp] or similar
                if isinstance(val, list) and len(val) >= 2:
                    ts = int(val[0])
                    v1 = float(val[1]) if val[1] is not None else 0.0
                    v2 = float(val[2]) if len(val) > 2 and val[2] is not None else None
                    v3 = float(val[3]) if len(val) > 3 and val[3] is not None else None
                    hourly_averages.append((ts, v1, v2, v3))
                elif isinstance(val, dict):
                    # fallback if garminconnect changes to return dicts
                    pass

            return RespirationData(
                calendar_date=cdate,
                lowest_respiration=raw.get("lowestRespirationValue"),
                highest_respiration=raw.get("highestRespirationValue"),
                avg_waking_respiration=raw.get("wakingRespirationValue"),
                avg_sleep_respiration=raw.get("sleepRespirationValue"),
                timeseries=timeseries,
                hourly_averages=hourly_averages,
            )
    except Exception as e:
        log.warning("Respiration data fetch failed for %s: %s", date_str, e)
    return None
