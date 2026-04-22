import sqlite3
from garmin_training_toolkit_sdk.weather.config import config

class WeatherDB:
    def __init__(self, db_path=None):
        self.db_path = db_path or config.db_path
        self._init_db()

    def _init_db(self):
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

    def save_daily(self, date, temp_avg, temp_min, temp_max, humidity, feels_like_avg, conditions):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO daily_weather 
            (date, temp_avg, temp_min, temp_max, humidity, feels_like_avg, conditions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (date, temp_avg, temp_min, temp_max, humidity, feels_like_avg, conditions))
        conn.commit()
        conn.close()

    def save_daily_batch(self, records):
        conn = sqlite3.connect(self.db_path)
        conn.executemany("""
            INSERT OR REPLACE INTO daily_weather 
            (date, temp_avg, temp_min, temp_max, humidity, feels_like_avg, conditions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, records)
        conn.commit()
        conn.close()

    def get_daily(self, date):
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
                "conditions": row[6]
            }
        return None

    def get_range(self, start_date, end_date):
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("""
            SELECT * FROM daily_weather 
            WHERE date >= ? AND date <= ?
            ORDER BY date
        """, (start_date, end_date))
        rows = cur.fetchall()
        conn.close()
        return [{
            "date": r[0],
            "temp_avg": r[1],
            "temp_min": r[2],
            "temp_max": r[3],
            "humidity": r[4],
            "feels_like_avg": r[5],
            "conditions": r[6]
        } for r in rows]

    def save_hourly(self, timestamp, temp, humidity, feels_like):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO hourly_weather (timestamp, temp, humidity, feels_like)
            VALUES (?, ?, ?, ?)
        """, (timestamp, temp, humidity, feels_like))
        conn.commit()
        conn.close()

    def get_hourly(self, timestamp):
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("SELECT * FROM hourly_weather WHERE timestamp = ?", (timestamp,))
        row = cur.fetchone()
        conn.close()
        if row:
            return {"timestamp": row[0], "temp": row[1], "humidity": row[2], "feels_like": row[3]}
        return None

    def save_config(self, key, value):
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()

    def get_config(self, key):
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None

db = WeatherDB()