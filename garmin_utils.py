#!/usr/bin/env python3
"""
Shared utilities for Garmin tools.
Handles token loading, authentication, and common configuration.
"""

import base64
import json
import logging
import os
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

TOKEN_LOCATIONS = [
    Path(__file__).parent / "garmin_tokens.json",
    Path(__file__).parent / "garmin-workout-uploader" / "garmin_tokens.json",
    Path.home() / ".garminconnect" / "garmin_tokens.json",
]

ENV_FILE = Path(__file__).parent / ".env"

RATE_LIMIT_DELAY = 10
MAX_RETRIES = 5
REQUEST_DELAY_MIN = 1.0
REQUEST_DELAY_MAX = 2.0


def find_token_file() -> Optional[Path]:
    """Find the token file in any known location."""
    for loc in TOKEN_LOCATIONS:
        if loc.exists():
            return loc
    return None


def load_env_file(env_path: Optional[Path] = None) -> dict:
    """Load credentials from .env file. Decodes base64 credentials if present."""
    if env_path is None:
        env_path = ENV_FILE
    
    prefs = {}
    if env_path.exists():
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
            Path(__file__).parent / "garmin-workout-uploader" / "garmin_tokens.json",
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
