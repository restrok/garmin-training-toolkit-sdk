# Garmin Training Toolkit SDK

A robust, type-safe Python SDK for extracting biometric data and telemetry from Garmin Connect.

## Purpose

This toolkit is designed as a raw data connector. It handles authentication, rate limiting, and data extraction from Garmin's unofficial APIs, returning clean, typed Pydantic models. It is built to be consumed by external Data Pipelines (like a Data Lakehouse) or AI systems (like LangGraph).

**Note:** This repository is strictly an SDK. It does not contain AI logic, training plan generators, or an API server (FastAPI).

## Installation

This project uses `uv` for dependency management.

```bash
# In your consumer project (if using uv):
uv add git+https://github.com/restrok/garmin-training-toolkit-sdk.git#subdirectory=garmin_training_toolkit_sdk
```

*Or for local development within this repository:*
```bash
cd garmin_training_toolkit_sdk
uv sync
```

## Quick Start

### 1. Authentication
Garmin uses session tokens. To log in and cache your session locally:

```bash
# Runs a headless browser to authenticate and save tokens
python3 garmin.py auth
```

### 2. Extracting Data (Python Example)

```python
import json
from garmin_training_toolkit_sdk.utils import get_authenticated_client, find_token_file
from garmin_training_toolkit_sdk.extractors import get_activities, get_activity_telemetry

# 1. Connect
token_file = find_token_file()
client = get_authenticated_client(token_file)

# 2. Extract Activity Summary (Pydantic model)
activities = get_activities(client, "2026-04-10", "2026-04-20")
latest = activities[0]
print(f"Latest run: {latest.name} ({latest.distance_m} meters)")

# 3. Extract Detailed Telemetry (Second-by-second data)
telemetry = get_activity_telemetry(client, latest.id)
print(f"Total ticks: {telemetry.metric_count}")

# Pydantic makes serialization easy
print(json.dumps(telemetry.ticks[0].model_dump(), indent=2))
```

## Available Extractors

All extractors return typed Pydantic models ensuring data reliability.

*   `get_activities(client, start_date, end_date)`
*   `get_activity_telemetry(client, activity_id)` -> Second-by-second telemetry (GPS, HR, Power, etc).
*   `get_hrv_data(client, start_date, end_date)`
*   `get_sleep_data(client, start_date, end_date)`
*   `get_readiness_data(client, date)`
*   `get_body_battery(client, date)`
*   `get_stress_data(client, date)`
*   `get_training_status(client, date)`

## Workout Management & Uploaders

The SDK provides robust logic for managing your Garmin calendar and uploading custom workout plans.

### 1. Uploading Workouts
Supports "Triple Redundancy" targets (Pace/HR/Power) required by modern Garmin watches to display intensity targets correctly.

The SDK includes a `load_workouts()` utility in `garmin_training_toolkit_sdk.uploaders.workouts`. To prevent pipeline noise, it returns an empty list `[]` if the internal `workouts.json` is missing.

```python
from garmin_training_toolkit_sdk.uploaders.workouts import create_workout, load_workouts

# 1. Load workouts (gracefully handles missing workouts.json)
workouts = load_workouts()

# 2. Create a workout dictionary (Triple Redundancy for Pace/HR targets)
workout_data = {
    "name": "Tempo Run",
    "duration": 2400,
    "steps": [
        {"type": "warmup", "duration": 600},
        {"type": "run", "duration": 1200, "target": "4:30 min/km"}
    ]
}
workout_dict = create_workout(workout_data)

# 3. Upload
client.upload_workout(workout_dict)
```

### 2. Calendar Management
Safely manage your schedule without affecting Garmin's "Auto Training Plans" (ATP).

```python
from garmin_training_toolkit_sdk.uploaders.calendar import clear_calendar_range, schedule_workout

# Clear a specific range (Safely skips Garmin native plans)
# Returns the integer count of successfully cleared items.
cleared_count = clear_calendar_range(client, "2026-05-01", "2026-05-31")
print(f"Removed {cleared_count} items from calendar.")

# Schedule a workout
schedule_workout(client, workout_id="12345", workout_date="2026-05-15")
```

## Testing & Mocks

The SDK includes a `MockGarminClient` to allow consumers to test their pipelines without hitting Garmin's rate limits or production APIs.

```python
from garmin_training_toolkit_sdk.testing.mock import MockGarminClient

mock_client = MockGarminClient()
# Use mock_client exactly like a Garmin() instance
```
