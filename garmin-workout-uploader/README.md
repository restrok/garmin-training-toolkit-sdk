# Garmin Workout Uploader

**Now use the main CLI instead:**

```bash
python3 garmin.py upload   # Upload workouts
python3 garmin.py auth    # Re-authenticate
```

## Legacy Commands (still work)

```bash
python garmin_workout_uploader.py      # Upload
python garmin_workout_uploader.py --list   # List
python garmin_auth_browser.py               # Auth
```

## Features

- Upload workouts to Garmin Connect
- Schedule workouts on your Garmin calendar
- List all scheduled workouts
- Clean old workouts from previous plans
- Browser-based authentication (bypasses Cloudflare rate limiting)
- Persistent token storage (re-authenticate only when tokens expire)

## Requirements

- Python 3.10+
- Chrome/Chromium browser (for Playwright authentication)
- `pydantic` (auto-installed with requirements)

## Setup

### 1. Clone or copy the project

```bash
cd garmin-workout-uploader
```

### 2. Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt

# Install Chromium for Playwright (one time)
playwright install chromium
```

### 4. Configure

Copy the example env file and edit with your training goals:

```bash
cp .env.example .env
nano .env
```

## Usage

### First time: Authenticate via browser

```bash
python garmin_auth_browser.py
```

This will:
1. Open a Chrome window
2. You log in with your Garmin credentials
3. Tokens are saved automatically
4. Window closes when done

### Upload workouts

```bash
python garmin_workout_uploader.py
```

Uploads and schedules all workouts defined in `WORKOUTS` list.

### List all workouts

```bash
python garmin_workout_uploader.py --list
```

Lists all workouts in your Garmin Connect account.

### Clean old workouts

```bash
# Clean all old workouts from previous plans
python garmin_workout_uploader.py --clean

# Clean old workouts for a specific month prefix
python garmin_workout_uploader.py --clean Apr
python garmin_workout_uploader.py --clean May
```

Removes old/stale workouts from previous training plans (keeps the newest version of each).

### Delete a specific workout

```bash
python garmin_workout_uploader.py --delete <workout_id>
```

## Customizing Workouts

Edit `garmin_workout_uploader.py` and modify the `WORKOUTS` list:

```python
WORKOUTS = [
    {
        "name": "Workout Name",
        "date": "2026-04-01",
        "description": "Description",
        "duration": 1800,  # seconds
        "steps": [
            ("warmup", 300),     # (type, duration)
            ("run", 1200),        # run = easy pace
            ("cooldown", 300),
        ]
    },
]
```

### Step types

- `warmup` - Warm up phase
- `run` - Easy run (Zone 2)
- `interval` - Intervals (use with distance in meters)
- `recovery` - Recovery between intervals
- `cooldown` - Cool down phase

### Example: Intervals

```python
{
    "name": "Intervals 6x800m",
    "date": "2026-04-15",
    "description": "6x800m at 5K pace",
    "duration": 2700,
    "steps": [
        ("warmup", 600),
        ("interval", 800, 90),   # 800m with 90s recovery
        ("interval", 800, 90),
        ("interval", 800, 90),
        ("interval", 800, 90),
        ("interval", 800, 90),
        ("interval", 800, 0),    # last interval, no recovery after
        ("cooldown", 300),
    ]
}
```

## Files

| File | Description |
|------|-------------|
| `garmin_auth_browser.py` | Browser-based authentication |
| `garmin_workout_uploader.py` | Main app - upload & schedule workouts |
| `requirements.txt` | Python dependencies |
| `.env.example` | Template for credentials |
| `.gitignore` | Git ignore file |

## How it works

1. **Browser Authentication**: Uses Playwright to open a real Chrome window for Garmin login, bypassing Cloudflare's bot detection.

2. **Token Storage**: OAuth tokens are saved to `~/.garminconnect/garmin_tokens.json` and reused for future sessions.

3. **Workout Upload**: Uses the `garminconnect` Python library to create and upload workouts via the Garmin Connect API.

4. **Scheduling**: Each workout is scheduled on your Garmin calendar for the specified date.

## Troubleshooting

### 429 Rate Limit Error

If you see "Rate limited" errors:
- Wait 1-4 hours before retrying
- Use browser authentication: `python garmin_auth_browser.py`

### Token Expired

When tokens expire:
```bash
python garmin_auth_browser.py
```

### Browser doesn't open

Make sure Chromium is installed:
```bash
playwright install chromium
```

## License

MIT
