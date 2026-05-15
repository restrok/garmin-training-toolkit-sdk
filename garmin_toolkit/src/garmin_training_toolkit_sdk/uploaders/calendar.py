import logging
from datetime import date, datetime
from typing import Any, Dict, List, Union

from garminconnect import Garmin

log = logging.getLogger(__name__)


def schedule_workout(
    garmin_client: Garmin, workout_id: str, workout_date: Union[str, date]
) -> Any:
    """Schedule a workout on the Garmin calendar.

    Args:
        garmin_client: The Garmin API client instance.
        workout_id: The ID of the workout to schedule.
        workout_date: The date to schedule the workout on.

    Returns:
        The result of the schedule operation.
    """
    if isinstance(workout_date, date):
        workout_date = workout_date.isoformat()
    log.info("Scheduling workout %s on %s", workout_id, workout_date)
    return garmin_client.schedule_workout(workout_id, workout_date)


def get_calendar_range(
    garmin_client: Garmin, start_date: Union[str, date], end_date: Union[str, date]
) -> List[Dict[str, Any]]:
    """Fetch all scheduled items between start_date and end_date (inclusive).

    Handles pagination across month boundaries internally.

    Args:
        garmin_client: The Garmin API client instance.
        start_date: The start date of the range.
        end_date: The end date of the range.

    Returns:
        A list of dictionary objects representing calendar items.
    """
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    # Fetch months covered by the range
    current = start_date.replace(day=1)
    months = []
    while current <= end_date:
        months.append((current.year, current.month))
        # Move to next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    all_items = []
    seen_ids = set()

    for year, month in months:
        log.debug("Fetching calendar for %d-%d", year, month)
        try:
            # Determine if client is the new SDK provider or the raw garminconnect client
            # The new SDK Provider has a get_scheduled_workouts that takes a date
            if hasattr(garmin_client, "get_scheduled_workouts"):
                # Try calling with date first (new standardized signature)
                try:
                    cal = garmin_client.get_scheduled_workouts(date(year, month, 1))
                except (TypeError, ValueError):
                    # Fallback to positional year, month (raw garminconnect client)
                    cal = garmin_client.get_scheduled_workouts(year, month)
            else:
                log.error("Client does not have get_scheduled_workouts method")
                continue

            if cal and "calendarItems" in cal:
                for item in cal["calendarItems"]:
                    item_id = item.get("calendarItemId") or item.get("id")
                    if item_id and item_id not in seen_ids:
                        all_items.append(item)
                        seen_ids.add(item_id)
        except Exception as e:
            log.error("Failed to fetch calendar for %d-%d: %s", year, month, e)

    # Filter by date range
    filtered_items = []
    for item in all_items:
        item_date_str = item.get("date")
        if not item_date_str:
            continue

        try:
            item_date = datetime.strptime(item_date_str, "%Y-%m-%d").date()
            if start_date <= item_date <= end_date:
                filtered_items.append(item)
        except ValueError:
            continue

    return filtered_items


def clear_calendar_range(
    garmin_client: Garmin, start_date: Union[str, date], end_date: Union[str, date]
) -> int:
    """Fetch all scheduled workouts between start_date and end_date and unschedule them.

    Safeguard: Skips any items containing an atpPlanId (Auto Training Plan)
    as these cause 403/404 errors.

    Args:
        garmin_client: The Garmin API client instance.
        start_date: The start date of the range.
        end_date: The end date of the range.

    Returns:
        The integer count of successfully cleared items.
    """
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    log.info("Clearing calendar from %s to %s", start_date, end_date)

    all_items = get_calendar_range(garmin_client, start_date, end_date)

    # Filter by date range and type
    to_unschedule = []
    for item in all_items:
        # Safeguard: Skip ATP plans
        if item.get("atpPlanId"):
            log.info(
                "Skipping ATP item '%s' on %s", item.get("title"), item.get("date")
            )
            continue

        to_unschedule.append(item)

    if not to_unschedule:
        log.info("No items found to clear in this range.")
        return 0

    log.info("Unscheduling %d items...", len(to_unschedule))
    cleared_count = 0
    for item in to_unschedule:
        calendar_item_id = item.get("calendarItemId") or item.get("id")
        title = item.get("title")
        item_date = item.get("date")

        if not calendar_item_id:
            log.warning(
                "Could not find ID for item '%s' on %s, skipping.", title, item_date
            )
            continue

        log.info("Unscheduling: %s on %s (ID: %s)", title, item_date, calendar_item_id)
        try:
            garmin_client.unschedule_workout(calendar_item_id)
            cleared_count += 1
        except Exception as e:
            log.error("Failed to unschedule item %s: %s", calendar_item_id, e)

    return cleared_count
