#!/usr/bin/env python3
"""
Shared utilities for Garmin tools.
Handles token loading, authentication, and common configuration.
"""

import base64
import json
import logging
import random
import time
from functools import wraps
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

TOKEN_LOCATIONS = [
    Path(__file__).parent.parent / "garmin_tokens",
    Path(__file__).parent / "garmin_tokens",
    Path.home() / ".garminconnect",
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
            
            raise last_exception
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


def get_authenticated_client(token_dir: Optional[Path] = None):
    """Get authenticated Garmin client using garminconnect native auth."""
    from pathlib import Path
    from garminconnect import Garmin
    
    # Check for tokens in standard location
    token_path = Path.home() / ".garminconnect" / "garmin_tokens.json"
    if not token_path.exists():
        raise Exception("Not authenticated. Run garmin.py auth first.")
    
    client = Garmin()
    try:
        client.client.load(str(token_path))
    except Exception as e:
        raise Exception(f"Failed to load tokens: {e}")
    
    log.info("Authenticated via garminconnect (native DI OAuth)")
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


def validate_workout(workout: dict) -> tuple[bool, Optional[str]]:
    """Validate a workout object from workouts.json."""
    required_fields = ["name", "date", "description", "duration", "steps"]
    
    for field in required_fields:
        if field not in workout:
            return False, f"Missing required field: {field}"
    
    if not isinstance(workout["steps"], list):
        return False, "Steps must be a list"
    
    if not workout["steps"]:
        return False, "Workout must have at least one step"
    
    valid_step_types = {"warmup", "cooldown", "run", "interval", "recovery"}
    
    for i, step in enumerate(workout["steps"]):
        if not isinstance(step, list):
            return False, f"Step {i}: must be a list"
        
        if len(step) < 2:
            return False, f"Step {i}: must have at least type and duration"
        
        step_type = step[0]
        if step_type not in valid_step_types:
            return False, f"Step {i}: invalid type '{step_type}'"
        
        try:
            float(step[1])
        except (ValueError, TypeError):
            return False, f"Step {i}: duration must be a number"
    
    return True, None


def validate_workouts_file(file_path: Path) -> tuple[bool, list]:
    """Validate entire workouts.json file."""
    errors = []
    
    if not file_path.exists():
        errors.append(f"File not found: {file_path}")
        return False, errors
    
    try:
        workouts = json.loads(file_path.read_text())
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
        return False, errors
    
    if not isinstance(workouts, list):
        errors.append("Root must be a list of workouts")
        return False, errors
    
    for i, workout in enumerate(workouts):
        valid, error = validate_workout(workout)
        if not valid:
            errors.append(f"Workout {i} ('{workout.get('name', 'unknown')}'): {error}")
    
    return len(errors) == 0, errors
