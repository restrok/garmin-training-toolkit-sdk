# Design Philosophy: Why build an SDK over garminconnect?

This document outlines the architectural decisions behind building the `garmin_toolkit` SDK instead of simply using the raw `garminconnect` Python library in our AI pipelines.

## The Problem with Raw API Wrappers

The `garminconnect` library is an excellent, low-level wrapper around Garmin's unofficial APIs. However, using it directly inside a Data Pipeline or an AI Agent (like LangGraph) introduces severe fragility:

1.  **Silent Failures (No Data Contracts):** `garminconnect` returns raw, nested JSON dictionaries. If Garmin silently changes an API response key from `"averageHR"` to `"avgHeartRate"`, the code using it will silently return `None`. This corrupts Vector Databases and causes AI models to hallucinate based on missing context.
2.  **Telemetry Compression:** Garmin does not return telemetry (second-by-second data) as clean key-value pairs. It returns a complex matrix of `metricDescriptors` (indexes) and flat arrays of values to save bandwidth. Parsing this requires complex mapping logic.
3.  **Coupling:** Mixing API-specific rate-limiting logic, token management, and JSON parsing directly into the reasoning loop of an AI agent violates the separation of concerns.

## The Solution: `garmin_toolkit` SDK

The `garmin_toolkit` acts as an anti-corruption layer (Data Connector) between Garmin's erratic API and our Enterprise AI Platform.

### 1. Strict Data Contracts (Pydantic)
By wrapping all outputs in Pydantic models (e.g., `TrainingStatusData`, `ActivityTelemetry`), the SDK guarantees the schema. 
*   **Fail Fast:** If Garmin changes their API structure, Pydantic throws a validation error immediately during extraction, rather than letting bad data quietly poison the Data Lake.
*   **Developer Experience:** IDEs provide auto-completion (e.g., `status.vo2max` instead of `status.get("vo2MaxValue")`).

### 2. The Telemetry "Decompressor"
The SDK absorbs the complexity of Garmin's matrix telemetry arrays. The `get_activity_telemetry` extractor automatically decodes the `metricDescriptors` and returns a flat, clean list of `ActivityTelemetryPoint` objects, instantly ready to be converted into Parquet files or pandas DataFrames.

### 3. "Batteries Included" (Read, Write, and Context)
While `garminconnect` handles basic HTTP requests, this toolkit provides a unified domain-driven interface:
*   **Extractors (Read):** Cleanly segregated by domain (`activities`, `biometrics`).
*   **Uploaders (Write):** Abstracted logic for scheduling custom workout JSONs back to Garmin's calendar.
*   **Weather (Context):** A bundled, local SQLite-backed OpenMeteo module to enrich workouts with historical weather data without relying on external cloud APIs.

## Conclusion

In a modern Data/AI architecture, `garminconnect` is simply the HTTP transport layer. The `garmin_toolkit` is the actual **Data Product**—providing clean, reliable, and strictly typed data contracts that external AI systems can blindly trust.
