import logging
from typing import List, Optional
from ..protocol.biometrics import HRVData, SleepData, ReadinessData, BodyBatteryData, StressData, TrainingStatusData
from ..protocol.user import UserProfile, BodyComposition

log = logging.getLogger(__name__)

def get_user_profile(garmin_client) -> Optional[UserProfile]:
    """Fetch user profile information by combining data from multiple endpoints."""
    try:
        profile = garmin_client.get_user_profile()
        settings = garmin_client.get_userprofile_settings()
        
        user_data = profile.get("userData", {})
        
        # Calculate age from birthDate
        age = None
        birth_date_str = user_data.get("birthDate")
        if birth_date_str:
            from datetime import datetime
            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
            today = datetime.now()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

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
            resting_hr=user_data.get("restingHeartRate")
        )
    except Exception as e:
        log.warning(f"User profile fetch failed: {e}")
    return None

def get_body_composition(garmin_client, start_date: str, end_date: str) -> List[BodyComposition]:
    """Fetch body composition data for a date range."""
    composition_records = []
    try:
        raw_composition = garmin_client.get_body_composition(start_date, end_date)
        if raw_composition and "allMetrics" in raw_composition:
            for m in raw_composition["allMetrics"]:
                composition_records.append(BodyComposition(
                    date=m.get("calendarDate"),
                    weight_kg=m.get("weight"),
                    bmi=m.get("bmi"),
                    fat_percentage=m.get("bodyFat"),
                    muscle_mass_kg=m.get("muscleMass"),
                    water_percentage=m.get("waterPercentage")
                ))
    except Exception as e:
        log.warning(f"Body composition fetch failed: {e}")
    return composition_records

def get_hrv_data(garmin_client, start_date: str, end_date: str) -> List[HRVData]:
    """Fetch HRV data for a given date range."""
    hrv_records = []
    try:
        raw_hrv = garmin_client.get_hrv_data(end_date)
        if raw_hrv:
            if isinstance(raw_hrv, list):
                for h in raw_hrv:
                    date = h.get("calendarDate")
                    if date and start_date <= date <= end_date:
                        hrv_records.append(HRVData(
                            date=date,
                            avg_hrv=h.get("averageHRV"),
                            min_hrv=h.get("minHRV"),
                            max_hrv=h.get("maxHRV")
                        ))
            elif isinstance(raw_hrv, dict):
                 date = raw_hrv.get("calendarDate")
                 if date and start_date <= date <= end_date:
                    hrv_records.append(HRVData(
                        date=date,
                        avg_hrv=raw_hrv.get("averageHRV"),
                        min_hrv=raw_hrv.get("minHRV"),
                        max_hrv=raw_hrv.get("maxHRV")
                    ))
    except Exception as e:
        log.warning(f"HRV data fetch failed: {e}")
    return hrv_records

def get_sleep_data(garmin_client, start_date: str, end_date: str) -> List[SleepData]:
    """Fetch sleep data by iterating through the date range with robust error handling."""
    from datetime import datetime, timedelta
    
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
                    log.info(f"Found sleep record for {date_str}")
                    
                    sleep_scores = dto.get("sleepScores", {})
                    overall_score = sleep_scores.get("overall", {}).get("value")
                    
                    def to_int(val):
                        if val is None:
                            return None
                        try:
                            return int(val)
                        except (ValueError, TypeError):
                            return None

                    sleep_records.append(SleepData(
                        date=dto.get("calendarDate", date_str),
                        start=to_int(dto.get("sleepStartTimestampGMT")),
                        end=to_int(dto.get("sleepEndTimestampGMT")),
                        duration_sec=to_int(dto.get("sleepTimeSeconds")),
                        deep_sec=to_int(dto.get("deepSleepSeconds")),
                        light_sec=to_int(dto.get("lightSleepSeconds")),
                        rem_sec=to_int(dto.get("remSleepSeconds")),
                        awake_sec=to_int(dto.get("awakeSleepSeconds")),
                        quality=to_int(overall_score)
                    ))
            except Exception:
                pass
            
            curr += timedelta(days=1)
    except Exception as e:
        log.warning(f"Error in sleep loop: {e}")
        
    return sleep_records

def get_readiness_data(garmin_client, date: str) -> List[ReadinessData]:
    readiness_records = []
    try:
        raw_readiness = garmin_client.get_morning_training_readiness(date)
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

def get_body_battery(garmin_client, date: str) -> Optional[BodyBatteryData]:
    """Fetch body battery data for a specific date."""
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
                    values_count=len(values)
                )
    except Exception as e:
        log.warning(f"Body battery fetch failed for {date}: {e}")
    return None

def get_stress_data(garmin_client, date: str) -> Optional[StressData]:
    """Fetch stress data for a specific date."""
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
                high_stress_duration_sec=raw_stress.get("highStressDuration")
            )
    except Exception as e:
        log.warning(f"Stress data fetch failed for {date}: {e}")
    return None

def get_training_status(garmin_client, date: str) -> Optional[TrainingStatusData]:
    """Fetch training status for a specific date."""
    try:
        raw_status = garmin_client.get_training_status(date)
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
