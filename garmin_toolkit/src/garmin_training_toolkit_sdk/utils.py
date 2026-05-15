#!/usr/bin/env python3
"""Shared utilities for Garmin tools.

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
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from .protocol.workouts import WorkoutPlan

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
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

F = TypeVar("F", bound=Callable[..., Any])


def retry_with_backoff(
    max_retries: int = MAX_RETRIES,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
) -> Callable[[F], F]:
    """Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retries.
        initial_delay: Initial delay between retries in seconds.
        backoff_factor: Multiplier for the delay after each retry.

    Returns:
        A decorator function.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_msg = str(e).lower()

                    delay = initial_delay * (backoff_factor**attempt)

                    if "429" in error_msg or "rate limit" in error_msg:
                        delay = min(delay + random.uniform(0, 10), 300)
                        log.warning(
                            "Rate limited. Retrying in %.0fs (attempt %d/%d)",
                            delay,
                            attempt + 1,
                            max_retries,
                        )
                    elif "portal" in error_msg or "cloudflare" in error_msg:
                        delay = min(delay + random.uniform(0, 15), 120)
                        log.warning(
                            "Cloudflare blocking. Retrying in %.0fs (attempt %d/%d)",
                            delay,
                            attempt + 1,
                            max_retries,
                        )
                    elif "timeout" in error_msg or "connection" in error_msg:
                        delay = min(delay, 60)
                        log.warning(
                            "Connection error. Retrying in %.0fs (attempt %d/%d)",
                            delay,
                            attempt + 1,
                            max_retries,
                        )
                    else:
                        if attempt < max_retries - 1:
                            log.warning(
                                "Error: %s. Retrying in %.0fs (attempt %d/%d)",
                                e,
                                delay,
                                attempt + 1,
                                max_retries,
                            )
                        else:
                            raise

                    time.sleep(delay)

            if last_exception:
                raise last_exception
            raise Exception("Retry failed without specific exception")

        return wrapper  # type: ignore

    return decorator


def refresh_if_unauthorized(func: F) -> F:
    """Decorator to automatically attempt a token refresh on 401.

    Args:
        func: The function to decorate.

    Returns:
        The decorated function.
    """

    @wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            error_msg = str(e).lower()
            if "401" in error_msg or "unauthorized" in error_msg:
                log.warning(
                    "401 Unauthorized in %s. Attempting token refresh...", func.__name__
                )

                token_path = getattr(self, "token_path", None) or find_token_file()
                if token_path and _refresh_garmin_session(token_path):
                    log.info(
                        "Refresh successful. Re-initializing client and retrying..."
                    )

                    # If the object has a client attribute, we should re-initialize it
                    if hasattr(self, "client"):
                        from garminconnect import Garmin

                        with open(token_path) as f:
                            tokens = json.load(f)
                        new_client = Garmin()
                        new_client.client.loads(json.dumps(tokens))
                        self.client = new_client

                    return func(self, *args, **kwargs)
            raise e

    return wrapper  # type: ignore


def safe_api_call(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Make an API call with retry and error handling.

    Args:
        func: The API function to call.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.

    Returns:
        The result of the API call.
    """

    @retry_with_backoff()
    def _call() -> Any:
        return func(*args, **kwargs)

    return _call()


def find_token_file() -> Optional[Path]:
    """Find the token file in any known location.

    Returns:
        The Path to the token file if found, None otherwise.
    """
    for loc in TOKEN_LOCATIONS:
        if loc.exists():
            return loc
    return None


def load_env_file(env_path: Optional[Path] = None) -> Dict[str, str]:
    """Load credentials from .env file.

    Args:
        env_path: Optional path to the .env file.

    Returns:
        A dictionary of environment variables.
    """
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


DI_CLIENT_IDS = (
    "GARMIN_CONNECT_MOBILE_ANDROID_DI_2025Q2",
    "GARMIN_CONNECT_MOBILE_ANDROID_DI_2024Q4",
    "GARMIN_CONNECT_MOBILE_ANDROID_DI",
    "GARMIN_CONNECT_MOBILE_IOS_DI",
)


def _refresh_garmin_session(token_file: Path) -> bool:
    """Attempt to refresh Garmin session using multiple client IDs.

    Args:
        token_file: Path to the token file.

    Returns:
        True if refresh was successful, False otherwise.
    """
    from garminconnect import Garmin

    if not token_file.exists():
        return False

    with open(token_file) as f:
        tokens = json.load(f)

    for client_id in DI_CLIENT_IDS:
        log.info("Attempting session refresh with client ID: %s", client_id)
        client = Garmin()
        try:
            client.client.loads(json.dumps(tokens))
            client.client.di_client_id = client_id
            client.client._refresh_di_token()

            new_tokens = json.loads(client.client.dumps())
            save_tokens(new_tokens)
            log.info("Successfully refreshed Garmin session using %s", client_id)
            return True
        except Exception as e:
            log.debug("Refresh failed with %s: %s", client_id, e)

    return False


def get_authenticated_client(token_file: Optional[Path] = None) -> Any:
    """Get authenticated Garmin client using saved tokens with self-healing.

    Args:
        token_file: Optional path to the token file.

    Returns:
        An authenticated Garmin client instance.

    Raises:
        Exception: If authentication fails.
    """
    from garminconnect import Garmin

    if token_file is None:
        token_file = find_token_file()

    if not token_file:
        raise Exception("Not authenticated. Run garmin_auth_browser.py first.")

    def _create_client() -> Garmin:
        with open(token_file) as f:
            tokens = json.load(f)
        client = Garmin()
        client.client.loads(json.dumps(tokens))
        return client

    client = _create_client()

    try:
        # Light test call to verify authentication
        client.get_userprofile_settings()
        log.info("Authenticated using tokens from %s", token_file)
        return client
    except Exception as e:
        error_msg = str(e).lower()
        if "401" in error_msg or "unauthorized" in error_msg:
            log.warning(
                "Authentication expired or unauthorized. Attempting self-healing refresh..."
            )
            if _refresh_garmin_session(token_file):
                log.info("Self-healing successful! Re-instantiating client.")
                return _create_client()

        log.error("Authentication failed and self-healing was not possible: %s", e)
        raise e


def save_tokens(tokens: Dict[str, Any], locations: Optional[List[Path]] = None) -> None:
    """Save tokens to specified locations with proper permissions.

    Args:
        tokens: A dictionary containing token information.
        locations: Optional list of Paths to save the tokens to.
    """
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
            log.info("Saved tokens to %s", loc)
        except Exception as e:
            log.warning("Failed to save tokens to %s: %s", loc, e)


def pace_to_ms(pace_str: str) -> float:
    """Convert a pace string (e.g., '5:30 min/km' or '5:30') to m/s.

    Args:
        pace_str: The pace string to convert.

    Returns:
        The pace in meters per second. Returns 0.0 if parsing fails.
    """
    try:
        # Extract time part (handles '5:30 min/km', '5:30/km', '5:30')
        match = re.search(r"(\d+):(\d+)", pace_str)
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
    """Convert power string (e.g., '250W', '250') to float watts.

    Args:
        power_str: The power string to convert.

    Returns:
        The power in watts as a float.
    """
    try:
        return float(re.sub(r"[^\d.]", "", str(power_str)))
    except ValueError:
        return 0.0


def validate_workout(workout: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate a workout object using Pydantic.

    Args:
        workout: The workout dictionary to validate.

    Returns:
        A tuple (is_valid, error_message).
    """
    from .protocol.workouts import WorkoutTemplate

    try:
        WorkoutTemplate(**workout)
        return True, None
    except Exception as e:
        return False, str(e)


def validate_workouts_file(file_path: Path) -> Tuple[bool, List[str]]:
    """Validate entire workouts.json file using Pydantic.

    Args:
        file_path: Path to the workouts.json file.

    Returns:
        A tuple (is_valid, list_of_errors).
    """
    errors = []

    if not file_path.exists():
        errors.append("File not found: %s" % file_path)
        return False, errors

    try:
        with open(file_path) as f:
            data = json.load(f)
        WorkoutPlan(data)
    except json.JSONDecodeError as e:
        errors.append("Invalid JSON: %s" % e)
        return False, errors
    except Exception as e:
        errors.append("Validation error: %s" % e)
        return False, errors

    return True, []
