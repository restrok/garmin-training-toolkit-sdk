# Garmin Connect Training System

A complete system for analyzing Garmin Connect data and generating personalized training plans with workout upload capability.

## Quick Start

```bash
# 1. Authenticate (browser opens - log in with Garmin credentials)
python3 garmin.py auth

# 2. Collect your data from Garmin Connect
python3 garmin.py collect

# 3. Analyze & Predict
python3 garmin.py progress      # Training stats
python3 garmin.py zones         # Personalized HR zones
python3 garmin.py recovery      # HRV & readiness
python3 garmin.py predict      # Race time predictions
python3 garmin.py best          # Best times

# 4. Generate & Upload Plan
python3 garmin.py plan    # Create training plan
python3 garmin.py upload  # Upload to Garmin Connect
```

---

## CLI Commands Reference

| Command | Description | Options |
|---------|-------------|---------|
| `auth` | Browser authentication | `--headless`, `--timeout 300` |
| `collect` | Fetch data from Garmin | (auto-auth if needed) |
| `progress` | Training statistics | `--days 90` |
| `zones` | Data-driven HR zones | |
| `recovery` | HRV & readiness | |
| `predict` | Race predictions | |
| `best` | Best race times | `--distance 10k`, `--limit 5` |
| `compare` | Plan vs training | |
| `export` | Full report | `--file output.md` |
| `plan` | Generate plan | |
| `upload` | Upload workouts | |

---

## Configuration (.env file)

Create `.env` in project root:

```env
# Training Goals
GOAL_RACE=10K
GOAL_DATE=2026-07-15
TRAINING_DAYS=3
MAX_SESSION_MINUTES=90

# Pace Targets (min:sec per km)
RACE_PACE_TARGET=5:30
EASY_PACE=6:00
TEMPO_PACE=5:45
INTERVAL_PACE=5:15
```

---

## Data Flow

```
garmin.py (CLI)
       │
       ├──► collect ──► garmin-analyzer/collector.py ──► garmin-analyzer/data/garmin_report.json
       │                       │
       │                       └──► garmin_report.md
       │
       ├──► plan ──► garmin-analyzer/plan_generator.py ──► garmin-workout-uploader/workouts.json
       │
       └──► upload ──► garmin-workout-uploader/garmin_workout_uploader.py ──► Garmin Connect
```

---

## Key Implementation Details

### HR Zones (Data-Driven)

Zones are calculated from actual running HR data percentiles, NOT generic formulas:

- **Z1 (Recovery)**: < 25th percentile - 5
- **Z2 (Easy)**: 25th percentile ± 5 (conversational)
- **Z3 (Tempo)**: 25th+6 to 75th percentile
- **Z4 (Threshold)**: 75th+1 to max-20
- **Z5 (Max)**: > max-20

### Race Predictions

Uses **Riegel formula**: `T2 = T1 × (D2/D1)^1.06`

- Takes median of best 3 runs (>=5km)
- More realistic than Garmin's optimistic predictions

### Training Plan

- 80/20 polarized structure (easy/hard)
- Deload weeks every 4th week
- Progressive overload
- Build → Peak → Taper phases
- Uses .env pace targets

### Token Management

Tokens saved to: `garmin_tokens.json` (root + uploader dir)

- Find via: `garmin_utils.find_token_file()`
- Load via: `garmin_utils.get_authenticated_client(token_file)`
- Auto-refresh on 401 errors

### API Rate Limits

- `REQUEST_DELAY_MIN = 1.0s`
- `REQUEST_DELAY_MAX = 2.0s`
- Retry with exponential backoff on 429 errors

---

## Workout Format (workouts.json)

```json
[
  {
    "name": "Easy Run 1",
    "date": "2026-04-13",
    "description": "Easy pace 6:00/km - building aerobic base",
    "duration": 2400,
    "steps": [
      ["warmup", 600, null],
      ["run", 1800, null],
      ["cooldown", 300, null]
    ]
  }
]
```

Step types: `warmup`, `cooldown`, `run`, `interval`, `recovery`

---

## For LLM Code Generation

When extending this codebase:

1. **Data source**: `garmin-analyzer/data/garmin_report.json` - contains all raw data
2. **Token handling**: Use `garmin_utils.find_token_file()` → `get_authenticated_client()`
3. **Auth refresh**: Check for "401" or "Unauthorized" in errors, re-run auth
4. **HR zones**: Always use percentile-based from actual data, not 220-age
5. **Predictions**: Use Riegel formula with median of best 3 runs
6. **Rate limits**: Always add delays between API calls

---

## Requirements

- Python 3.10+
- Playwright (`pip install playwright`, `playwright install chromium`)
- garminconnect library

```bash
pip install garminconnect requests-oauthlib playwright
playwright install chromium
```

---

## File Structure

```
garmin/
├── .env                              # Configuration
├── garmin.py                         # Main CLI (all commands)
├── garmin_auth.py                    # Browser authentication
├── garmin_utils.py                   # Shared utilities
├── garmin_tokens.json                # Auth tokens
├── garmin-analyzer/
│   ├── collector.py                  # Data collection
│   ├── plan_generator.py             # Plan generation
│   └── data/
│       ├── garmin_report.json         # Raw data
│       └── garmin_report.md          # Human report
└── garmin-workout-uploader/
    ├── garmin_workout_uploader.py    # Upload/schedule
    └── workouts.json                 # Current plan
```
