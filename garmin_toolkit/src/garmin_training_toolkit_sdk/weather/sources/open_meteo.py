"""Open-Meteo API implementation for weather data."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests  # type: ignore

from garmin_training_toolkit_sdk.weather.config import config
from garmin_training_toolkit_sdk.weather.storage.sqlite import db

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

log = logging.getLogger(__name__)


def geocode_city(city_name: str) -> Dict[str, Any]:
    """Geocodes a city name to coordinates.

    Args:
        city_name: The name of the city.

    Returns:
        Dict[str, Any]: A dictionary containing city name, latitude, longitude, and country.

    Raises:
        ValueError: If the city is not found.
    """
    params = {"name": city_name, "count": 1, "language": "en", "format": "json"}
    resp = requests.get(GEOCODE_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("results"):
        raise ValueError(f"City not found: {city_name}")
    r = data["results"][0]
    return {
        "city": r["name"],
        "lat": r["latitude"],
        "lon": r["longitude"],
        "country": r.get("country", ""),
    }


def fetch_historical(
    lat: float, lon: float, start_date: str, end_date: str
) -> List[Tuple[Any, ...]]:
    """Fetches historical weather data from Open-Meteo.

    Args:
        lat: Latitude.
        lon: Longitude.
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).

    Returns:
        List[Tuple[Any, ...]]: A list of tuples containing daily weather records.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": (
            "temperature_2m_mean,temperature_2m_max,temperature_2m_min,"
            "relative_humidity_2m_mean,apparent_temperature_mean"
        ),
        "timezone": "auto",
    }
    resp = requests.get(ARCHIVE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    daily = data.get("daily", {})
    records = []
    for i, date in enumerate(daily.get("time", [])):
        temp_max = daily.get("temperature_2m_max", [None])[i]
        records.append(
            (
                date,
                daily.get("temperature_2m_mean", [None])[i],
                daily.get("temperature_2m_min", [None])[i],
                temp_max,
                int(daily.get("relative_humidity_2m_mean", [None])[i] or 0),
                daily.get("apparent_temperature_mean", [None])[i],
                _infer_conditions(temp_max),
            )
        )
    return records


def _infer_conditions(temp_max: Optional[float]) -> str:
    """Infers weather conditions based on maximum temperature.

    Args:
        temp_max: Maximum temperature.

    Returns:
        str: Description of weather conditions.
    """
    if temp_max is None:
        return "unknown"
    if temp_max < 10:
        return "cold"
    if temp_max < 20:
        return "cool"
    if temp_max < 28:
        return "mild"
    if temp_max < 33:
        return "warm"
    return "hot"


def set_city(city: str) -> Dict[str, Any]:
    """Sets the city and its coordinates in configuration and database.

    Args:
        city: The name of the city.

    Returns:
        Dict[str, Any]: Geocoded city information.
    """
    geo = geocode_city(city)
    config.save(city, geo["lat"], geo["lon"])
    db.save_config("city", city)
    db.save_config("lat", str(geo["lat"]))
    db.save_config("lon", str(geo["lon"]))
    return geo


def get_city_coords() -> Optional[Dict[str, Any]]:
    """Retrieves city coordinates from configuration or database.

    Returns:
        Optional[Dict[str, Any]]: City coordinates if found, else None.
    """
    if config.lat and config.lon:
        return {"city": config.city, "lat": float(config.lat), "lon": float(config.lon)}
    city = db.get_config("city")
    lat = db.get_config("lat")
    lon = db.get_config("lon")
    if city and lat and lon:
        return {"city": city, "lat": float(lat), "lon": float(lon)}
    return None


def backfill_last_year() -> int:
    """Backfills weather data for the last year.

    Returns:
        int: Number of records backfilled.

    Raises:
        ValueError: If the city is not configured.
    """
    coords = get_city_coords()
    if not coords:
        raise ValueError("City not configured. Run set_city() first.")
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    records = fetch_historical(coords["lat"], coords["lon"], start_date, end_date)
    db.save_daily_batch(records)
    return len(records)
