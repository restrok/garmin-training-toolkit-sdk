# Garmin Connect Analyzer

Collects all your Garmin Connect data and generates a comprehensive analysis report with your training goals.

## Purpose

This tool generates a report that can be shared with an LLM to create personalized training plans. It includes your training preferences and realistic pace targets.

## Workflow

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  garmin-analyzer │ ──▶ │ garmin_report.md │ ──▶ │     LLM      │
│   collector.py   │     │              │     │ (you/Claude) │
└─────────────────┘     └──────────────┘     └─────────────┘
                                                      │
                                                      ▼
                                              Training Plan
                                                      │
                                                      ▼
┌──────────────────────┐     ┌─────────────────┐
│ garmin-workout-uploader │ ◀── │   JSON workouts   │
│ garmin_workout_uploader │     │                 │
└──────────────────────┘     └─────────────────┘
```

## Setup

```bash
cd garmin-analyzer
pip install -r requirements.txt
```

## Usage

### 1. Configure Training Goals

Edit `../.env` (in the parent `garmin/` directory):

```env
# Training Goals
GOAL_RACE=10K
GOAL_DATE=2026-07-15
TRAINING_DAYS=3
MAX_SESSION_MINUTES=90
INJURY_HISTORY=none
PREFERRED_TIME=afternoon
PREFERRED_LOCATION=Tigre

# Pace Targets (based on current fitness)
RACE_PACE_TARGET=5:30
EASY_PACE=6:00
TEMPO_PACE=5:45
INTERVAL_PACE=5:15
```

### 2. Authenticate (if needed)

```bash
cd ../garmin-workout-uploader
python garmin_auth_browser.py
```

### 3. Collect Data

```bash
cd ../garmin-analyzer
python collector.py
```

This creates:
- `data/garmin_report.json` - Raw data
- `data/garmin_report.md` - Human-readable report with your goals

### 4. Share with LLM

**Important:** Share these files with the LLM:
1. `garmin_report.md` - Your data and goals
2. `TRAINING_GUIDELINES.md` - Training principles
3. `RESEARCH_TRAINING_PRINCIPLES.md` - Scientific research

Ask the LLM: "Create a training plan based on this data and guidelines"

The report now includes instructions to read these files, but sharing them directly ensures the LLM follows the scientific guidelines.

### 5. Create Workouts

Copy the training plan to `garmin-workout-uploader/garmin_workout_uploader.py` and upload:

```bash
cd ../garmin-workout-uploader
python garmin_workout_uploader.py
```

## Files

| File | Description |
|------|-------------|
| `collector.py` | Fetches data from Garmin Connect, reads .env preferences |
| `requirements.txt` | Python dependencies |
| `data/` | Output directory |
| `TRAINING_GUIDELINES.md` | Scientific training principles |
| `RESEARCH_TRAINING_PRINCIPLES.md` | Research summary |

## Data Collected

- Activities (running, cycling, etc.) - last 90 days
- Sleep data
- Body composition (weight)
- HRV (Heart Rate Variability)
- Training readiness
- Race predictions
- Fitness metrics (VO2 Max)
- Training goals & pace targets from .env
