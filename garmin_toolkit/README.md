# Garmin Training Toolkit SDK

A robust, type-safe Python SDK for extracting biometric data and telemetry from Garmin Connect, optimized for autonomous agents and LLM tool-calling.

## Architecture: LLM-Native & Vendor-Agnostic

The SDK has been refactored to prioritize:
1.  **Semantic Naming:** No more cryptic Garmin fields. We use `min_target`, `max_target`, and `target_type`.
2.  **Provider Pattern:** Logic is decoupled from Garmin-specific APIs. You can now use a standardized `BaseBiometricProvider` interface.
3.  **Agent-First Schema:** Pydantic models include exhaustive descriptions and `Literal` types, allowing LLMs to understand the tool requirements with 100% accuracy from the JSON schema alone.

## Installation

This project uses `uv` for dependency management.

```bash
# In your consumer project:
uv add git+https://github.com/restrok/garmin-training-toolkit-sdk.git#subdirectory=garmin_toolkit
```

## Quick Start

### 1. Standardized Provider Interface

The recommended way to use the SDK is via the `GarminProvider`.

```python
from datetime import date
from garmin_training_toolkit_sdk.core.garmin import GarminProvider

# 1. Initialize (automatically finds local tokens)
provider = GarminProvider()

# 2. Fetch Activities (Returns vendor-agnostic Protocol models)
activities = provider.get_activities(date(2026, 4, 1), date(2026, 4, 30))
latest = activities[0]
print(f"Activity: {latest.name} | Distance: {latest.distance_m}m")

# 3. Get Telemetry
telemetry = provider.get_telemetry(latest.id)
print(f"Sample HR: {telemetry.ticks[0].hr_bpm} bpm")
```

### 2. LLM-Native Workouts (Agent Friendly)

Agents can create workouts using semantic naming or high-level helpers.

```python
from garmin_training_toolkit_sdk.protocol.workouts import create_simple_hr_workout

# High-level helper for Agents
workout = create_simple_hr_workout(
    name="Z2 Recovery Run",
    date="2026-05-01",
    bpm_min=135,
    bpm_max=145,
    duration_mins=45
)

# Upload via the provider
report = provider.upload_training_plan(workout)
print(f"Status: {report.message}")
```

## Tool Factory (For AI Agents)

If you are building an AI Agent (LangChain, AutoGPT, etc.), you can use the `ToolFactory` to generate a standardized set of tools from any provider.

```python
from garmin_training_toolkit_sdk.core.factory import ToolFactory
from garmin_training_toolkit_sdk.core.garmin import GarminProvider

provider = GarminProvider()
tools = ToolFactory.create_tools(provider)

# These tools have semantic descriptions that LLMs love:
# - get_activities
# - get_telemetry
# - upload_training_plan
```

## Directory Structure

*   `core/`: Provider implementations (Garmin, etc.) and the Tool Factory.
*   `protocol/`: Vendor-agnostic Pydantic models (Activity, Telemetry, Workout).
*   `extractors/`: Low-level data extraction logic.
*   `uploaders/`: Logic for calendar and workout management.

## Testing & Mocks

The SDK includes a `MockGarminClient` in `testing/mock.py` to allow consumers to test their pipelines without hitting Garmin's production APIs.

```python
from garmin_training_toolkit_sdk.testing.mock import MockGarminClient
# Use in your unit tests to avoid rate limits
```
