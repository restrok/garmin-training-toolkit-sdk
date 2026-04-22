import requests
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from weather.storage.sqlite import db
from weather.sources.open_meteo import get_city_coords

CURRENT_URL = "https://api.open-meteo.com/v1/forecast"

def fetch_current(lat=None, lon=None):
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
        "timezone": "auto"
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
        "feels_like": current.get("apparent_temperature")
    }
    db.save_hourly(timestamp, record["temp"], record["humidity"], record["feels_like"])
    return record

def fetch_by_coords(lat, lon):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature",
        "timezone": "auto"
    }
    resp = requests.get(CURRENT_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    current = data.get("current", {})
    return {
        "timestamp": datetime.now().isoformat(),
        "temp": current.get("temperature_2m"),
        "humidity": current.get("relative_humidity_2m"),
        "feels_like": current.get("apparent_temperature")
    }