# Garmin Connect Training System

Complete system for analyzing Garmin data and generating personalized training plans.

```
garmin/
├── .env                      # Credentials & training goals
├── garmin_tokens.json        # Auth tokens (auto-generated)
├── garmin-analyzer/          # Data collection & analysis
└── garmin-workout-uploader/  # Workout upload & management
```

## Quick Start

### 1. Setup

```bash
# Configure your training goals
nano .env
```

### 2. Authenticate (one time)

```bash
# Activate virtual environment
source garmin-workout-uploader/.venv/bin/activate

cd garmin-workout-uploader
python garmin_auth_browser.py
```

### 3. Collect & Analyze

```bash
cd ../garmin-analyzer
python collector.py
```

### 4. Generate Training Plan

1. Open `garmin-analyzer/data/garmin_report.md`
2. Share with an LLM (e.g., Claude)
3. Ask: "Create a 10K training plan based on this data"

### 5. Upload Workouts

1. Copy the training plan to `garmin-workout-uploader/workouts.json`
2. Run:
```bash
cd ../garmin-workout-uploader
python garmin_workout_uploader.py
```

## Commands

### garmin-analyzer
```bash
source ../garmin-workout-uploader/.venv/bin/activate
python collector.py    # Collect data & generate report
```

### garmin-workout-uploader
```bash
source .venv/bin/activate
python garmin_workout_uploader.py           # Upload workouts
python garmin_workout_uploader.py --list   # List all workouts
python garmin_workout_uploader.py --clean  # Remove old workouts
python garmin_auth_browser.py               # Re-authenticate
```

## Training Goals (.env)

```env
GOAL_RACE=10K
GOAL_DATE=2026-07-15
TRAINING_DAYS=3
MAX_SESSION_MINUTES=90
RACE_PACE_TARGET=5:30
EASY_PACE=6:00
TEMPO_PACE=5:45
INTERVAL_PACE=5:15
```

## Project Structure

```
garmin/
├── .env                           # Your credentials & goals
├── garmin-analyzer/
│   ├── collector.py               # Data collector
│   ├── data/
│   │   ├── garmin_report.md       # Analysis report
│   │   └── garmin_report.json     # Raw data
│   ├── TRAINING_GUIDELINES.md     # Training rules
│   └── RESEARCH_TRAINING_PRINCIPLES.md
└── garmin-workout-uploader/
    ├── garmin_workout_uploader.py # Main uploader
    ├── garmin_auth_browser.py     # Browser auth
    └── WORKOUTS = [...]          # Your training plan
```

## Requirements

- Python 3.10+ (see `.python-version`)
- Chrome/Chromium (for browser authentication)
- Virtual environment (included in repo)

Install dependencies:
```bash
cd garmin-workout-uploader
pip install -r requirements.txt
playwright install chromium
```
