# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Self-Healing Authentication**: Implemented a robust mechanism to handle `401 Unauthorized` errors.
  - Added `_refresh_garmin_session` utility to rotate through multiple Android/iOS Client IDs (`DI_CLIENT_IDS`) during token refresh.
  - Updated `get_authenticated_client` to automatically attempt a session refresh if the initial authentication fails.
- **Verification Suite**: Added comprehensive unit tests for authentication resilience in `tests/test_auth_self_healing.py`.

## [0.4.0] - 2026-04-25

### Added
- **LLM-Native SDK Refactor**: Redesigned models and protocols to be optimized for LLM consumption (LangGraph/AutoGPT).
- **Standardized Provider Interface**: Unified the way extractors and uploaders interact with the Garmin API.
- **Semantic Protocol**: Renamed models to `protocol` to emphasize the data contract.

### Changed
- **Metadata Enhancement**: Added rich metadata and semantic keys to workout and activity models for better AI reasoning.

## [0.3.1] - 2026-04-25

### Fixed
- PyPI publishing configuration and dependency resolution.

## [0.3.0] - 2026-04-25

### Added
- Token search priority logic to support multiple environment configurations.
- Debug utility for deep inspection of Garmin activity JSON payloads.
