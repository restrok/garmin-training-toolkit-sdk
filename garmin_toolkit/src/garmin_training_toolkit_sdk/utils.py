#!/usr/bin/env python3
"""
Shared utilities for Garmin tools.
Handles token loading, authentication, and common configuration.
"""

import base64
import json
import logging
import random
import re
import time
from functools import wraps
from pathlib import Path
from typing import Optional

from .protocol.workouts import WorkoutPlan

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

TOKEN_LOCATIONS = [
    Path.home() / ".garminconnect" / "garmin_tokens.json",
    Path(__file__).parent.parent / "garmin_tokens.json",
    Path(__file__).parent.parent.parent / "garmin_tokens.json",
    Path(__file__).parent.parent.parent.parent / "garmin_tokens.json",
    Path(__file__).parent.parent.parent.parent.parent / "garmin_tokens.json",
    Path(__file__).parent / "garmin_tokens.json",
    Path.cwd() / "garmin_tokens.json",
    Path.cwd().parent / "garmin_tokens.json",
]

ENV_FILE = Path(__file__).parent / ".env"

RATE_LIMIT_DELAY = 10
MAX_RETRIES = 5
REQUEST_DELAY_MIN = 1.0
REQUEST_DELAY_MAX = 2.0


def retry_with_backoff(max_retries: int = MAX_RETRIES, initial_delay: float = 1.0, backoff_factor: float = 2.0):
    """Decorator for retrying functions with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_msg = str(e).lower()
                    
                    delay = initial_delay * (backoff_factor ** attempt)
                    
                    if "429" in error_msg or "rate limit" in error_msg:
                        delay = min(delay + random.uniform(0, 10), 300)
                        log.warning(f"Rate limited. Retrying in {delay:.0f}s (attempt {attempt + 1}/{max_retries})")
                    elif "portal" in error_msg or "cloudflare" in error_msg:
                        delay = min(delay + random.uniform(0, 15), 120)
                        log.warning(f"Cloudflare blocking. Retrying in {delay:.0f}s (attempt {attempt + 1}/{max_retries})")
                    elif "timeout" in error_msg or "connection" in error_msg:
                        delay = min(delay, 60)
                        log.warning(f"Connection error. Retrying in {delay:.0f}s (attempt {attempt + 1}/{max_retries})")
                    else:
                        if attempt < max_retries - 1:
                            log.warning(f"Error: {e}. Retrying in {delay:.0f}s (attempt {attempt + 1}/{max_retries})")
                        else:
                            raise
                    
                    time.sleep(delay)
            
            if last_exception:
                raise last_exception
            raise Exception("Retry failed without specific exception")
        return wrapper
    return decorator


def safe_api_call(func, *args, **kwargs):
    """Make an API call with retry and error handling."""
    @retry_with_backoff()
    def _call():
        return func(*args, **kwargs)
    return _call()


def find_token_file() -> Optional[Path]:
    """Find the token file in any known location."""
    for loc in TOKEN_LOCATIONS:
        if loc.exists():
            return loc
    return None


def load_env_file(env_path: Optional[Path] = None) -> dict:
    """Load credentials from .env file. Searches root and subdirectories."""
    if env_path is None:
        # Search in multiple locations
        search_paths = [
            Path(__file__).parent / ".env",
            Path(__file__).parent / "garmin-workout-uploader" / ".env",
        ]
        for path in search_paths:
            if path.exists():
                env_path = path
                break
    
    prefs = {}
    if env_path and env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    value = value.strip('"').strip("'")
                    if key.endswith("_B64"):
                        try:
                            value = base64.b64decode(value).decode()
                            key = key[:-4]
                        except Exception:
                            pass
                    prefs[key] = value
    return prefs


def get_authenticated_client(token_file: Optional[Path] = None):
    """Get authenticated Garmin client using saved tokens."""
    from garminconnect import Garmin
    
    if token_file is None:
        token_file = find_token_file()
    
    if not token_file:
        raise Exception("Not authenticated. Run garmin_auth_browser.py first.")
    
    with open(token_file) as f:
        tokens = json.load(f)
    
    client = Garmin()
    client.client.loads(json.dumps(tokens))
    log.info(f"Authenticated using tokens from {token_file}")
    return client


def save_tokens(tokens: dict, locations: Optional[list] = None):
    """Save tokens to specified locations with proper permissions."""
    token_data = json.dumps(tokens, indent=2)
    
    if locations is None:
        locations = [
            Path(__file__).parent / "garmin_tokens.json",
            Path(__file__).parent.parent / "garmin_tokens.json",
            Path.home() / ".garminconnect" / "garmin_tokens.json",
        ]
    
    for loc in locations:
        try:
            loc.parent.mkdir(parents=True, exist_ok=True)
            loc.write_text(token_data)
            loc.chmod(0o600)
            log.info(f"Saved tokens to {loc}")
        except Exception as e:
            log.warning(f"Failed to save tokens to {loc}: {e}")


def pace_to_ms(pace_str: str) -> float:
    """
    Convert a pace string (e.g., '5:30 min/km' or '5:30') to m/s.
    Returns 0.0 if parsing fails.
    """
    try:
        # Extract time part (handles '5:30 min/km', '5:30/km', '5:30')
        match = re.search(r'(\d+):(\d+)', pace_str)
        if not match:
            return 0.0
        
        minutes = int(match.group(1))
        seconds = int(match.group(2))
        total_seconds_per_km = minutes * 60 + seconds
        
        if total_seconds_per_km == 0:
            return 0.0
            
        return 1000.0 / total_seconds_per_km
    except (ValueError, AttributeError):
        return 0.0

def power_to_watts(power_str: str) -> float:
    """Convert power string (e.g., '250W', '250') to float watts."""
    try:
        return float(re.sub(r'[^\d.]', '', str(power_str)))
    except ValueError:
        return 0.0

def validate_workout(workout: dict) -> tuple[bool, Optional[str]]:
    """Validate a workout object using Pydantic."""
    from .protocol.workouts import WorkoutTemplate
    try:
        WorkoutTemplate(**workout)
        return True, None
    except Exception as e:
        return False, str(e)


def validate_workouts_file(file_path: Path) -> tuple[bool, list]:
    """Validate entire workouts.json file using Pydantic."""
    errors = []
    
    if not file_path.exists():
        errors.append(f"File not found: {file_path}")
        return False, errors
    
    try:
        with open(file_path) as f:
            data = json.load(f)
        WorkoutPlan(data)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
        return False, errors
    except Exception as e:
        errors.append(f"Validation error: {e}")
        return False, errors
    
    return True, []
