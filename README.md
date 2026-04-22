# Garmin Training Toolkit SDK

A robust, type-safe Python SDK for extracting biometric data and telemetry from Garmin Connect.

## Purpose

This toolkit is designed as a raw data connector. It handles authentication, rate limiting, and data extraction from Garmin's unofficial APIs, returning clean, typed Pydantic models. It is built to be consumed by external Data Pipelines (like a Data Lakehouse) or AI systems (like LangGraph).

**Note:** This repository is strictly an SDK. It does not contain AI logic, training plan generators, or an API server (FastAPI).

## Installation

This project uses `uv` for dependency management.

```bash
# In your consumer project (if using uv):
uv add git+https://github.com/restrok/garmin-training-toolkit-sdk.git#subdirectory=garmin_toolkit
```

*Or for local development within this repository:*
```bash
cd garmin_toolkit
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
from garmin_toolkit.utils import get_authenticated_client, find_token_file
from garmin_toolkit.extractors import get_activities, get_activity_telemetry

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

## Included Modules

While the core focus is extraction, the SDK also bundles:
*   **`garmin_toolkit.uploaders`**: Logic for uploading custom workout plans back to Garmin.
*   **`garmin_toolkit.weather`**: A local SQLite-backed weather module (OpenMeteo) to enrich activity data with historical weather context.
