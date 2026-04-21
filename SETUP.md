# ⚠️ IMPORTANT: Always use virtual environment

## Quick Start

```bash
# 1. Navigate to project
cd /path/to/garmin-training-toolkit

# 2. Activate venv (REQUIRED - do this every time)
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate      # Windows

# 3. Install dependencies (venv must be active!)
pip install -r requirements.txt

# 4. Authenticate (first time only)
python3 garmin.py auth

# 5. Use the toolkit
python3 garmin.py collect
python3 garmin.py upload
python3 garmin.py analyze
```

## What is virtual environment?

A virtual environment (`venv`) creates an isolated Python environment for this project. It keeps project dependencies separate from your system Python and other projects.

## Why use venv?

- **No system pollution** - packages don't affect other Python projects
- **Version control** - exact dependency versions, reproducible
- **Clean removal** - just delete `.venv` folder to clean up
- **Shared machines** - safe to use on shared systems

## NEVER do this:

```bash
# ❌ DON'T install packages globally
pip install garminconnect
pip install -r requirements.txt  # (without venv active!)

# ✅ ALWAYS use venv
source .venv/bin/activate
pip install -r requirements.txt
```

## If you see packages in ~/.local or system pip:

```bash
# Uninstall the problematic packages
pip uninstall garminconnect garth curl_cffi -y

# Then reinstall in venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Troubleshooting

**"Module not found" errors:**
```bash
# Make sure venv is activated
source .venv/bin/activate
python3 garmin.py ...
```

**Auth fails with rate limit:**
- Wait a few minutes before retrying
- Garmin limits API calls
- Use `--headless` flag for faster login

## Project Structure

```
garmin-training-toolkit/
├── .venv/                    # Virtual environment (gitignored)
├── garmin.py                 # Main CLI
├── garmin_utils.py           # Shared utilities
├── garmin_auth.py            # Authentication
├── garmin_tokens/            # Token storage
├── requirements.txt         # Dependencies
└── ...
```