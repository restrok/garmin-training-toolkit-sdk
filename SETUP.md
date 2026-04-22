# ⚠️ IMPORTANT: Environment Setup

This project uses `uv` for modern, fast dependency management. Do not use legacy `pip install -r requirements.txt` workflows.

## Quick Start (with `uv`)

```bash
# 1. Navigate to project
cd /path/to/garmin-training-toolkit-sdk

# 2. Sync dependencies (uv automatically creates the virtual environment)
cd garmin_toolkit
uv sync

# 3. Authenticate (first time only)
uv run python3 ../garmin.py auth

# 4. Run an ingestion test
uv run python3 ../example_ingestion.py
```

## Why use `uv`?

- **Blazing Fast:** Written in Rust, it resolves and installs dependencies in milliseconds.
- **Automatic venv:** You don't need to manually `source .venv/bin/activate`. Using `uv run <command>` automatically executes within the isolated environment.
- **Strict Resolution:** Ensures exact dependency versions across all machines.

## Project Structure

```
garmin-training-toolkit-sdk/
├── garmin.py                 # Main CLI (Authentication only)
├── example_ingestion.py      # Example of how to use the SDK
├── garmin_toolkit/           # The core SDK Package
│   ├── pyproject.toml        # Dependencies definition
│   ├── src/                  # Extractors and Pydantic Models
│   └── uv.lock               # Dependency lockfile
└── ...
```