import requests
from datetime import datetime, timedelta
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from weather.config import config
from weather.storage.sqlite import db

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

def geocode_city(city_name):
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
        "country": r.get("country", "")
    }

def fetch_historical(lat, lon, start_date, end_date):
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_mean,temperature_2m_max,temperature_2m_min,relative_humidity_2m_mean,apparent_temperature_mean",
        "timezone": "auto"
    }
    resp = requests.get(ARCHIVE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    daily = data.get("daily", {})
    records = []
    for i, date in enumerate(daily.get("time", [])):
        records.append((
            date,
            daily.get("temperature_2m_mean", [None])[i],
            daily.get("temperature_2m_min", [None])[i],
            daily.get("temperature_2m_max", [None])[i],
            int(daily.get("relative_humidity_2m_mean", [None])[i] or 0),
            daily.get("apparent_temperature_mean", [None])[i],
            _infer_conditions(daily.get("temperature_2m_max", [None])[i])
        ))
    return records

def _infer_conditions(temp_max):
    if temp_max is None:
        return "unknown"
    if temp_max < 10:
        return "cold"
    elif temp_max < 20:
        return "cool"
    elif temp_max < 28:
        return "mild"
    elif temp_max < 33:
        return "warm"
    else:
        return "hot"

def set_city(city):
    geo = geocode_city(city)
    config.save(city, geo["lat"], geo["lon"])
    db.save_config("city", city)
    db.save_config("lat", str(geo["lat"]))
    db.save_config("lon", str(geo["lon"]))
    return geo

def get_city_coords():
    if config.lat and config.lon:
        return {"city": config.city, "lat": float(config.lat), "lon": float(config.lon)}
    city = db.get_config("city")
    lat = db.get_config("lat")
    lon = db.get_config("lon")
    if city and lat and lon:
        return {"city": city, "lat": float(lat), "lon": float(lon)}
    return None

def backfill_last_year():
    coords = get_city_coords()
    if not coords:
        raise ValueError("City not configured. Run set_city() first.")
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    records = fetch_historical(coords["lat"], coords["lon"], start_date, end_date)
    db.save_daily_batch(records)
    return len(records)