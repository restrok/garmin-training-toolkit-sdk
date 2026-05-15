"""Current weather data from Open-Meteo (replaces original OpenWeather source)."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import requests  # type: ignore

from garmin_training_toolkit_sdk.weather.sources.open_meteo import get_city_coords
from garmin_training_toolkit_sdk.weather.storage.sqlite import db

CURRENT_URL = "https://api.open-meteo.com/v1/forecast"

log = logging.getLogger(__name__)


def fetch_current(
    lat: Optional[float] = None, lon: Optional[float] = None
) -> Dict[str, Any]:
    """Fetches current weather data.

    Args:
        lat: Optional latitude. If not provided, uses configured city coordinates.
        lon: Optional longitude. If not provided, uses configured city coordinates.

    Returns:
        Dict[str, Any]: Current weather data record.

    Raises:
        ValueError: If city is not configured and coordinates are not provided.
    """
    if not lat or not lon:
        coords = get_city_coords()
        if not coords:
            raise ValueError("City not configured. Run set_city() first.")
        lat = coords["lat"]
        lon = coords["lon"]
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature",
        "timezone": "auto",
    }
    resp = requests.get(CURRENT_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    current = data.get("current", {})
    timestamp = datetime.now().isoformat()
    record = {
        "timestamp": timestamp,
        "temp": current.get("temperature_2m"),
        "humidity": current.get("relative_humidity_2m"),
        "feels_like": current.get("apparent_temperature"),
    }
    db.save_hourly(timestamp, record["temp"], record["humidity"], record["feels_like"])
    return record


def fetch_by_coords(lat: float, lon: float) -> Dict[str, Any]:
    """Fetches current weather data by coordinates.

    Args:
        lat: Latitude.
        lon: Longitude.

    Returns:
        Dict[str, Any]: Current weather data record.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature",
        "timezone": "auto",
    }
    resp = requests.get(CURRENT_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    current = data.get("current", {})
    return {
        "timestamp": datetime.now().isoformat(),
        "temp": current.get("temperature_2m"),
        "humidity": current.get("relative_humidity_2m"),
        "feels_like": current.get("apparent_temperature"),
    }
