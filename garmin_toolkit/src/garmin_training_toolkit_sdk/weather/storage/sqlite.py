"""SQLite storage implementation for weather data."""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from garmin_training_toolkit_sdk.weather.config import config


class WeatherDB:
    """Handles SQLite database operations for weather data."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initializes the WeatherDB with a database path.

        Args:
            db_path: Path to the SQLite database file. Defaults to config.db_path.
        """
        self.db_path: Path = db_path or config.db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initializes the database schema if it does not exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_weather (
                date TEXT PRIMARY KEY,
                temp_avg REAL,
                temp_min REAL,
                temp_max REAL,
                humidity INTEGER,
                feels_like_avg REAL,
                conditions TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hourly_weather (
                timestamp TEXT PRIMARY KEY,
                temp REAL,
                humidity INTEGER,
                feels_like REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.commit()
        conn.close()

    def save_daily(
        self,
        date: str,
        temp_avg: float,
        temp_min: float,
        temp_max: float,
        humidity: int,
        feels_like_avg: float,
        conditions: str,
    ) -> None:
        """Saves daily weather data.

        Args:
            date: The date string (YYYY-MM-DD).
            temp_avg: Average temperature.
            temp_min: Minimum temperature.
            temp_max: Maximum temperature.
            humidity: Relative humidity percentage.
            feels_like_avg: Average apparent temperature.
            conditions: Weather conditions description.
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT OR REPLACE INTO daily_weather 
            (date, temp_avg, temp_min, temp_max, humidity, feels_like_avg, conditions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (date, temp_avg, temp_min, temp_max, humidity, feels_like_avg, conditions),
        )
        conn.commit()
        conn.close()

    def save_daily_batch(self, records: List[Tuple[Any, ...]]) -> None:
        """Saves a batch of daily weather records.

        Args:
            records: A list of tuples containing weather data.
        """
        conn = sqlite3.connect(self.db_path)
        conn.executemany(
            """
            INSERT OR REPLACE INTO daily_weather 
            (date, temp_avg, temp_min, temp_max, humidity, feels_like_avg, conditions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            records,
        )
        conn.commit()
        conn.close()

    def get_daily(self, date: str) -> Optional[Dict[str, Any]]:
        """Retrieves daily weather data for a specific date.

        Args:
            date: The date string (YYYY-MM-DD).

        Returns:
            Optional[Dict[str, Any]]: A dictionary of weather data if found, else None.
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("SELECT * FROM daily_weather WHERE date = ?", (date,))
        row = cur.fetchone()
        conn.close()
        if row:
            return {
                "date": row[0],
                "temp_avg": row[1],
                "temp_min": row[2],
                "temp_max": row[3],
                "humidity": row[4],
                "feels_like_avg": row[5],
                "conditions": row[6],
            }
        return None

    def get_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Retrieves daily weather data for a date range.

        Args:
            start_date: Start date string (YYYY-MM-DD).
            end_date: End date string (YYYY-MM-DD).

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing weather data.
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            """
            SELECT * FROM daily_weather 
            WHERE date >= ? AND date <= ?
            ORDER BY date
        """,
            (start_date, end_date),
        )
        rows = cur.fetchall()
        conn.close()
        return [
            {
                "date": r[0],
                "temp_avg": r[1],
                "temp_min": r[2],
                "temp_max": r[3],
                "humidity": r[4],
                "feels_like_avg": r[5],
                "conditions": r[6],
            }
            for r in rows
        ]

    def save_hourly(
        self, timestamp: str, temp: float, humidity: int, feels_like: float
    ) -> None:
        """Saves hourly weather data.

        Args:
            timestamp: The timestamp string.
            temp: Temperature.
            humidity: Relative humidity percentage.
            feels_like: Apparent temperature.
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT OR REPLACE INTO hourly_weather (timestamp, temp, humidity, feels_like)
            VALUES (?, ?, ?, ?)
        """,
            (timestamp, temp, humidity, feels_like),
        )
        conn.commit()
        conn.close()

    def get_hourly(self, timestamp: str) -> Optional[Dict[str, Any]]:
        """Retrieves hourly weather data for a specific timestamp.

        Args:
            timestamp: The timestamp string.

        Returns:
            Optional[Dict[str, Any]]: A dictionary of weather data if found, else None.
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            "SELECT * FROM hourly_weather WHERE timestamp = ?", (timestamp,)
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return {
                "timestamp": row[0],
                "temp": row[1],
                "humidity": row[2],
                "feels_like": row[3],
            }
        return None

    def save_config(self, key: str, value: str) -> None:
        """Saves a configuration key-value pair to the database.

        Args:
            key: Configuration key.
            value: Configuration value.
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value)
        )
        conn.commit()
        conn.close()

    def get_config(self, key: str) -> Optional[str]:
        """Retrieves a configuration value from the database.

        Args:
            key: Configuration key.

        Returns:
            Optional[str]: Configuration value if found, else None.
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None


db = WeatherDB()
