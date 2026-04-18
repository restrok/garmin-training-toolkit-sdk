#!/usr/bin/env python3
"""
SQLite database for Garmin training data persistence.
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
log = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "data" / "garmin_data.db"


def get_db() -> sqlite3.Connection:
    """Get database connection, creating schema if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection):
    """Create tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY,
            activity_id INTEGER UNIQUE,
            name TEXT,
            type TEXT,
            date TEXT,
            duration_sec REAL,
            distance_m REAL,
            avg_hr REAL,
            max_hr REAL,
            avg_pace REAL,
            calories REAL,
            elevation_gain REAL,
            vo2max REAL,
            synced_at TEXT
        );
        
        CREATE TABLE IF NOT EXISTS planned_workouts (
            id INTEGER PRIMARY KEY,
            name TEXT,
            date TEXT,
            description TEXT,
            duration_sec INTEGER,
            steps_json TEXT,
            created_at TEXT,
            status TEXT DEFAULT 'pending'
        );
        
        CREATE TABLE IF NOT EXISTS completed_workouts (
            id INTEGER PRIMARY KEY,
            planned_id INTEGER,
            name TEXT,
            date TEXT,
            activity_id INTEGER,
            actual_duration_sec REAL,
            actual_distance_m REAL,
            avg_hr REAL,
            completed_at TEXT,
            FOREIGN KEY (planned_id) REFERENCES planned_workouts(id)
        );
        
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY,
            date TEXT UNIQUE,
            vo2max REAL,
            fitness_age REAL,
            weight REAL,
            resting_hr REAL,
            hrv_avg REAL,
            training_readiness INTEGER,
            training_status TEXT,
            collected_at TEXT
        );
        
        CREATE TABLE IF NOT EXISTS sleep (
            id INTEGER PRIMARY KEY,
            date TEXT UNIQUE,
            duration_sec REAL,
            deep_sec REAL,
            light_sec REAL,
            rem_sec REAL,
            awake_sec REAL,
            quality TEXT,
            collected_at TEXT
        );
        
        CREATE INDEX IF NOT EXISTS idx_activities_date ON activities(date);
        CREATE INDEX IF NOT EXISTS idx_metrics_date ON metrics(date);
        CREATE INDEX IF NOT EXISTS idx_sleep_date ON sleep(date);
    """)


def save_activities(activities: list[dict]):
    """Save activities to database."""
    conn = get_db()
    now = datetime.now().isoformat()
    
    for a in activities:
        conn.execute("""
            INSERT OR REPLACE INTO activities 
            (activity_id, name, type, date, duration_sec, distance_m, avg_hr, max_hr, 
             avg_pace, calories, elevation_gain, vo2max, synced_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            a.get("id"), a.get("name"), a.get("type"), a.get("date"),
            a.get("duration_sec"), a.get("distance_m"), a.get("avg_hr"),
            a.get("max_hr"), a.get("avg_pace"), a.get("calories"),
            a.get("elevation_gain"), a.get("vo2max"), now
        ))
    
    conn.commit()
    log.info(f"Saved {len(activities)} activities")


def save_metrics(metrics: dict, date: str):
    """Save metrics for a specific date."""
    conn = get_db()
    now = datetime.now().isoformat()
    
    conn.execute("""
        INSERT OR REPLACE INTO metrics 
        (date, vo2max, fitness_age, weight, resting_hr, hrv_avg, 
         training_readiness, training_status, collected_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        date, metrics.get("vo2max"), metrics.get("fitness_age"),
        metrics.get("weight"), metrics.get("resting_hr"), metrics.get("hrv_avg"),
        metrics.get("training_readiness"), metrics.get("training_status"), now
    ))
    
    conn.commit()


def save_sleep(sleep_data: list[dict]):
    """Save sleep records."""
    conn = get_db()
    now = datetime.now().isoformat()
    
    for s in sleep_data:
        conn.execute("""
            INSERT OR REPLACE INTO sleep
            (date, duration_sec, deep_sec, light_sec, rem_sec, awake_sec, 
             quality, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            s.get("date"), s.get("duration_sec"), s.get("deep_sec"),
            s.get("light_sec"), s.get("rem_sec"), s.get("awake_sec"),
            s.get("quality"), now
        ))
    
    conn.commit()
    log.info(f"Saved {len(sleep_data)} sleep records")


def save_planned_workout(workout: dict):
    """Save a planned workout."""
    conn = get_db()
    now = datetime.now().isoformat()
    
    conn.execute("""
        INSERT INTO planned_workouts (name, date, description, duration_sec, steps_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        workout.get("name"), workout.get("date"), workout.get("description"),
        workout.get("duration"), json.dumps(workout.get("steps")), now
    ))
    
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def mark_workout_completed(planned_id: int, activity: dict):
    """Mark a planned workout as completed with actual data."""
    conn = get_db()
    now = datetime.now().isoformat()
    
    conn.execute("""
        UPDATE planned_workouts SET status = 'completed' WHERE id = ?
    """, (planned_id,))
    
    conn.execute("""
        INSERT INTO completed_workouts 
        (planned_id, name, date, activity_id, actual_duration_sec, actual_distance_m, avg_hr, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        planned_id, activity.get("name"), activity.get("date"),
        activity.get("activity_id"), activity.get("duration_sec"),
        activity.get("distance_m"), activity.get("avg_hr"), now
    ))
    
    conn.commit()


def get_activities_since(date: str) -> list[dict]:
    """Get activities since a specific date."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM activities WHERE date >= ? ORDER BY date DESC",
        (date,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_vo2max_history(days: int = 90) -> list[dict]:
    """Get VO2 max history."""
    conn = get_db()
    rows = conn.execute("""
        SELECT date, vo2max FROM metrics 
        WHERE vo2max IS NOT NULL 
        ORDER BY date DESC LIMIT ?
    """, (days,)).fetchall()
    return [dict(r) for r in rows]


def get_progress_report() -> dict:
    """Generate progress report from database."""
    conn = get_db()
    
    # Total activities
    total = conn.execute("SELECT COUNT(*) FROM activities").fetchone()[0]
    
    # Running stats
    running = conn.execute("""
        SELECT COUNT(*) as count, SUM(distance_m)/1000 as dist, SUM(duration_sec)/3600 as time
        FROM activities WHERE type = 'running'
    """).fetchone()
    
    # Recent weekly averages
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    this_week = conn.execute("""
        SELECT COUNT(*) as runs, SUM(distance_m)/1000 as dist
        FROM activities WHERE type = 'running' AND date >= ?
    """, (week_ago,)).fetchone()
    
    # VO2 max trend
    vo2max = get_vo2max_history(30)
    
    return {
        "total_activities": total,
        "total_runs": running["count"] or 0,
        "total_distance_km": round(running["dist"] or 0, 1),
        "total_hours": round(running["time"] or 0, 1),
        "this_week_runs": this_week["runs"] or 0,
        "this_week_km": round(this_week["dist"] or 0, 1),
        "vo2max_trend": vo2max,
    }


def get_pending_workouts() -> list[dict]:
    """Get planned workouts that haven't been completed."""
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM planned_workouts 
        WHERE status = 'pending' AND date >= date('now')
        ORDER BY date
    """).fetchall()
    return [dict(r) for r in rows]
