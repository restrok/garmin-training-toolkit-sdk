# Design Philosophy: The Agent-First SDK

This document outlines the architectural decisions behind the `garmin_training_toolkit_sdk`. The SDK is designed to be the "Standard Interface" for biometric data, specifically optimized for **Autonomous AI Agents** and **Data Lakehouses**.

## The Problem: Brand Complexity & LLM Hallucinations

Biometric providers (Garmin, Suunto, Whoop) use proprietary, often cryptic APIs. For an AI Agent (like a Biometric Coach), these present two major hurdles:
1.  **Cognitive Load:** An LLM shouldn't have to know that `targetValueOne` means `min_heart_rate`. This leads to hallucinations and incorrect tool calls.
2.  **Vendor Lock-in:** Changing from Garmin to another brand usually requires refactoring the entire agent's tool-calling logic.

## The Solution: LLM-Native & Provider Pattern

The `garmin_training_toolkit_sdk` acts as an **Anti-Corruption Layer** that hides brand-specific complexity behind a unified "Common Language."

### 1. LLM-Native Data Contracts (Semantic Pydantic)
The SDK doesn't just return data; it returns data with **intent**. 
*   **Semantic Naming:** We use `min_target` and `max_target`. These names are intuitive for LLMs, allowing them to map user intent (e.g., "Set a recovery pace of 6:00") directly to the schema.
*   **Self-Documenting Schemas:** Every field in our `protocol/` package includes a `Field(description="...")`. When an agent inspects the tool, it receives a built-in manual on how to use it.
*   **Strict Typing:** Using `Literal["heart.rate.zone", "speed.zone"]` ensures the agent sees exactly which strings are valid, eliminating guesswork.

### 2. The Provider Pattern (Vendor Agnostic)
The SDK introduces the `BaseBiometricProvider` abstract interface.
*   **Unified Interface:** Whether you are fetching telemetry or uploading a workout, the methods are identical regardless of the hardware.
*   **The Tool Factory:** The `ToolFactory` can generate a set of tools from any provider. For an AI Agent, a "Garmin Tool" and a "Suunto Tool" will look identical, requiring zero changes to the agent's logic.

### 3. Protocol over Models
We renamed the `models/` package to `protocol/`. This signifies that these are not just data structures, but a **shared communication protocol**. Any biometric data, regardless of source, is translated into this protocol before reaching the consumer.

### 4. Robustness & Verification
*   **Fail Fast:** Pydantic validation ensures that bad data from a provider is caught at the source.
*   **Triple Redundancy:** For complex operations like Garmin workout uploads, the SDK handles the intricate JSON requirements (targets, zones, IDs) internally, exposing only a clean interface to the agent. See [GARMIN_API_QUIRKS.md](GARMIN_API_QUIRKS.md) for implementation details.

## Conclusion

In a world of autonomous agents, an SDK is more than just an API wrapper—it's a **Translator**. The `garmin_training_toolkit_sdk` provides the clean, reliable, and semantically rich "Common Language" that AI systems need to interact with the physical world of biometrics.
