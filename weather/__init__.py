from datetime import datetime

from .config import config
from .storage.sqlite import db
from .sources.open_meteo import set_city, get_city_coords, backfill_last_year
from .sources.openweather import fetch_current, fetch_by_coords

def init(city):
    coords = set_city(city)
    print(f"City set to {coords['city']} ({coords['lat']}, {coords['lon']})")
    return coords

def get_for_date(date_str):
    date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    record = db.get_daily(date)
    if record:
        return record
    return None

def get_historical_range(start_date, end_date):
    return db.get_range(start_date, end_date)

def get_current():
    return fetch_current()

def get_by_coords(lat, lon):
    return fetch_by_coords(lat, lon)

def get_for_activity(activity_date, lat=None, lon=None):
    date_str = activity_date[:10] if isinstance(activity_date, str) else activity_date.strftime("%Y-%m-%d")
    record = db.get_daily(date_str)
    if record:
        return record
    if lat and lon:
        return fetch_by_coords(lat, lon)
    return None

def is_configured():
    return config.is_configured()

def get_summary():
    coords = get_city_coords()
    if not coords:
        return {"configured": False}
    return {
        "configured": True,
        "city": coords["city"],
        "lat": coords["lat"],
        "lon": coords["lon"]
    }

def get_month_summary(date_str):
    date = datetime.strptime(date_str, "%Y-%m-%d")
    year = date.year
    month = date.month
    start_date = f"{year}-{month:02d}-01"
    import calendar
    end_date = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
    records = get_historical_range(start_date, end_date)
    if not records:
        prev_year = year - 1
        start_date = f"{prev_year}-{month:02d}-01"
        end_date = f"{prev_year}-{month:02d}-{calendar.monthrange(prev_year, month)[1]}"
        records = get_historical_range(start_date, end_date)
    if not records:
        return None
    temps = [r["temp_avg"] for r in records if r["temp_avg"]]
    max_temps = [r["temp_max"] for r in records if r["temp_max"]]
    return {
        "month": f"{year}-{month:02d}",
        "avg_temp": sum(temps) / len(temps) if temps else None,
        "max_temp": max(max_temps) if max_temps else None,
        "days": len(records)
    }

__all__ = [
    "init",
    "set_city",
    "get_city_coords",
    "backfill_last_year",
    "get_for_date",
    "get_historical_range",
    "get_current",
    "get_by_coords",
    "get_for_activity",
    "is_configured",
    "get_summary",
    "get_month_summary"
]