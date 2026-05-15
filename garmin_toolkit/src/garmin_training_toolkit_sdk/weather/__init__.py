"""Weather module for fetching and storing weather data."""

import calendar
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .config import config
from .sources.open_meteo import backfill_last_year, get_city_coords, set_city
from .sources.openweather import fetch_by_coords, fetch_current
from .storage.sqlite import db


def init(city: str) -> Dict[str, Any]:
    """Initializes the weather module for a specific city.

    Args:
        city: The name of the city.

    Returns:
        Dict[str, Any]: Geocoded city information.
    """
    coords = set_city(city)
    print(f"City set to {coords['city']} ({coords['lat']}, {coords['lon']})")
    return coords


def get_for_date(date_str: str) -> Optional[Dict[str, Any]]:
    """Retrieves weather data for a specific date.

    Args:
        date_str: The date string (YYYY-MM-DD).

    Returns:
        Optional[Dict[str, Any]]: Weather data if found, else None.
    """
    date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    return db.get_daily(date)


def get_historical_range(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Retrieves weather data for a date range.

    Args:
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).

    Returns:
        List[Dict[str, Any]]: A list of daily weather records.
    """
    return db.get_range(start_date, end_date)


def get_current() -> Dict[str, Any]:
    """Retrieves current weather data.

    Returns:
        Dict[str, Any]: Current weather data record.
    """
    return fetch_current()


def get_by_coords(lat: float, lon: float) -> Dict[str, Any]:
    """Retrieves current weather data by coordinates.

    Args:
        lat: Latitude.
        lon: Longitude.

    Returns:
        Dict[str, Any]: Current weather data record.
    """
    return fetch_by_coords(lat, lon)


def get_for_activity(
    activity_date: Union[str, datetime],
    lat: Optional[float] = None,
    lon: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieves weather data for an activity.

    Args:
        activity_date: The date of the activity.
        lat: Optional latitude.
        lon: Optional longitude.

    Returns:
        Optional[Dict[str, Any]]: Weather data if found, else None.
    """
    if isinstance(activity_date, str):
        date_str = activity_date[:10]
    else:
        date_str = activity_date.strftime("%Y-%m-%d")

    record = db.get_daily(date_str)
    if record:
        return record
    if lat is not None and lon is not None:
        return fetch_by_coords(lat, lon)
    return None


def is_configured() -> bool:
    """Checks if the weather module is configured.

    Returns:
        bool: True if configured, False otherwise.
    """
    return config.is_configured()


def get_summary() -> Dict[str, Any]:
    """Returns a summary of the weather configuration.

    Returns:
        Dict[str, Any]: Configuration summary.
    """
    coords = get_city_coords()
    if not coords:
        return {"configured": False}
    return {
        "configured": True,
        "city": coords["city"],
        "lat": coords["lat"],
        "lon": coords["lon"],
    }


def get_month_summary(date_str: str) -> Optional[Dict[str, Any]]:
    """Returns a summary of weather data for a specific month.

    Args:
        date_str: A date string within the desired month (YYYY-MM-DD).

    Returns:
        Optional[Dict[str, Any]]: Monthly weather summary if records exist, else None.
    """
    date = datetime.strptime(date_str, "%Y-%m-%d")
    year = date.year
    month = date.month
    start_date = f"{year}-{month:02d}-01"
    _, last_day = calendar.monthrange(year, month)
    end_date = f"{year}-{month:02d}-{last_day}"

    records = get_historical_range(start_date, end_date)
    if not records:
        prev_year = year - 1
        start_date = f"{prev_year}-{month:02d}-01"
        _, last_day = calendar.monthrange(prev_year, month)
        end_date = f"{prev_year}-{month:02d}-{last_day}"
        records = get_historical_range(start_date, end_date)

    if not records:
        return None

    temps = [r["temp_avg"] for r in records if r["temp_avg"] is not None]
    max_temps = [r["temp_max"] for r in records if r["temp_max"] is not None]

    return {
        "month": f"{year}-{month:02d}",
        "avg_temp": sum(temps) / len(temps) if temps else None,
        "max_temp": max(max_temps) if max_temps else None,
        "days": len(records),
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
    "get_month_summary",
]
