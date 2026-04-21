import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent

class Config:
    def __init__(self):
        load_dotenv(PROJECT_ROOT / ".env")
        self.city = os.getenv("WEATHER_CITY", "")
        self.lat = os.getenv("WEATHER_LAT", "")
        self.lon = os.getenv("WEATHER_LON", "")
        self.db_path = PROJECT_ROOT / "weather" / "weather.db"

    def is_configured(self):
        return bool(self.city)

    def save(self, city, lat=None, lon=None):
        self.city = city
        if lat:
            self.lat = str(lat)
        if lon:
            self.lon = str(lon)
        self._write_env()

    def _write_env(self):
        env_path = PROJECT_ROOT / ".env"
        lines = []
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if not line.startswith("WEATHER_"):
                        lines.append(line.rstrip())

        lines.append(f"WEATHER_CITY={self.city}")
        if self.lat:
            lines.append(f"WEATHER_LAT={self.lat}")
        if self.lon:
            lines.append(f"WEATHER_LON={self.lon}")

        with open(env_path, "w") as f:
            f.write("\n".join(filter(None, lines)) + "\n")

config = Config()