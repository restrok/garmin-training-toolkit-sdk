# Garmin Training Toolkit SDK

A high-performance, strictly typed Python SDK for extracting biometric data, high-resolution telemetry, and managing complex workout plans on Garmin Connect.

## Purpose

This toolkit serves as a professional-grade data connector for the Garmin ecosystem. It abstracts the complexities of Garmin's unofficial APIs, handling authentication, session management, and rate limiting, while parsing raw responses into clean, validated **Pydantic v2** models.

It is purpose-built for:
- **Data Engineering:** Powering Data Lakes or Warehouse systems with high-fidelity biometric history.
- **AI/ML Pipelines:** Providing structured health and performance context for LLM-based coaching or predictive analysis.
- **Quantified Self:** Bridging the gap between Garmin's closed ecosystem and modern, type-safe Pythonic workflows.

## Key Features

- **Strictly Typed:** 100% Pydantic v2 models for all domain entities (Activities, Telemetry, HRV, Sleep, Training Readiness, etc.).
- **Rich Biometrics:** Capture advanced metrics including HRV Baselines/Status, Sleep Scores, Body Battery, and Stress levels.
- **High-Res Telemetry:** Extraction of second-by-second data (GPS, Heart Rate, Power, Cadence, Temperature) from activity records.
- **Workout Management:** Programmatic creation and uploading of structured workout plans with support for nested repeat groups, specific targets (HR zones, Pace, Power), and calendar scheduling.
- **Local Weather Engine:** Integrated SQLite-backed module using **Open-Meteo** for historical weather enrichment of activities.
- **Engineering Excellence:** Developed using the **Google Python Style Guide**, enforced via `ruff` and `mypy`.

## Installation

This project uses `uv` for lightning-fast dependency management and isolation.

```bash
# Add as a dependency to your project:
uv add git+https://github.com/restrok/garmin-training-toolkit-sdk.git#subdirectory=garmin_toolkit
```

## Engineering Standards

We maintain a production-grade codebase to ensure reliability in critical data pipelines:
- **Style:** Adherence to the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html).
- **Quality:** Continuous linting and formatting via `ruff`.
- **Type Safety:** 100% type coverage verified with strict `mypy` configurations.
- **Testing:** Comprehensive test suite leveraging `pytest` and localized mocks.

## Quick Start

### 1. Authentication
Garmin utilizes session-based authentication. Use the interactive CLI tool to initialize and cache your tokens:
```bash
# Launches an interactive menu to choose your preferred authentication method
python3 garmin.py auth
```
The toolkit supports three authentication methods:
- **Terminal:** Direct email and password login.
- **Browser:** Automated login using a headless browser (bypasses Cloudflare).
- **Manual:** Paste an SSO ticket from your web browser (most reliable for restricted environments).

### 2. Data Extraction Example
```python
from garmin_training_toolkit_sdk.utils import get_authenticated_client, find_token_file
from garmin_training_toolkit_sdk.extractors.biometrics import get_hrv_data

# 1. Connect using cached tokens
client = get_authenticated_client(find_token_file())

# 2. Extract HRV data (returns Pydantic models with baseline and status)
hrv_history = get_hrv_data(client, "2026-05-01", "2026-05-15")

for record in hrv_history:
    print(f"Date: {record.date} | Avg HRV: {record.avg_hrv}ms | Status: {record.status}")
```

### 3. Uploading Workouts
```python
from garmin_training_toolkit_sdk.uploaders.workouts import upload_workout
from garmin_training_toolkit_sdk.protocol.workouts import WorkoutTemplate, WorkoutStep

# Define and push custom interval sessions directly to your device
# (See examples for complex RepeatGroup and Target implementations)
```

## Core Modules

- **`extractors`**: Robust handlers for pulling Activities, Telemetry, Daily Biometrics (Sleep, HRV, Stress, Readiness), and User Profile data.
- **`weather`**: A complete local engine for historical weather context. Includes SQLite storage for caching and Open-Meteo integration for license-free historical backfills.
- **`uploaders`**: Specialized logic for pushing data back to Garmin, including a Workout creator and a Calendar scheduler.
- **`protocol`**: The source of truth for our data models, ensuring consistent schemas across the entire SDK.

## Development

```bash
# Setup environment
cd garmin_toolkit
uv sync

# Quality checks
uv run pytest        # Execute test suite
uv run ruff check .  # Check style and linting
uv run mypy .        # Verify type safety
```

---
*Disclaimer: This project is an independent tool and is not affiliated with, authorized, maintained, sponsored, or endorsed by Garmin Ltd. or any of its affiliates.*
