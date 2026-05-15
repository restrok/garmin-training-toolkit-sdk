"""Configuration management for the weather module."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent


class Config:
    """Configuration class for weather settings."""

    def __init__(self) -> None:
        """Initializes the Config class by loading environment variables."""
        load_dotenv(PROJECT_ROOT / ".env")
        self.city: str = os.getenv("WEATHER_CITY", "")
        self.lat: str = os.getenv("WEATHER_LAT", "")
        self.lon: str = os.getenv("WEATHER_LON", "")
        self.db_path: Path = PROJECT_ROOT / "weather" / "weather.db"

    def is_configured(self) -> bool:
        """Checks if the weather module is configured with a city.

        Returns:
            bool: True if a city is configured, False otherwise.
        """
        return bool(self.city)

    def save(
        self, city: str, lat: Optional[float] = None, lon: Optional[float] = None
    ) -> None:
        """Saves the weather configuration.

        Args:
            city: The name of the city.
            lat: The latitude of the city.
            lon: The longitude of the city.
        """
        self.city = city
        if lat:
            self.lat = str(lat)
        if lon:
            self.lon = str(lon)
        self._write_env()

    def _write_env(self) -> None:
        """Writes the weather configuration to the .env file."""
        env_path = PROJECT_ROOT / ".env"
        lines = []
        if env_path.exists():
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    if not line.startswith("WEATHER_"):
                        lines.append(line.rstrip())

        lines.append(f"WEATHER_CITY={self.city}")
        if self.lat:
            lines.append(f"WEATHER_LAT={self.lat}")
        if self.lon:
            lines.append(f"WEATHER_LON={self.lon}")

        with open(env_path, "w", encoding="utf-8") as f:
            f.write("\n".join(filter(None, lines)) + "\n")


config = Config()
