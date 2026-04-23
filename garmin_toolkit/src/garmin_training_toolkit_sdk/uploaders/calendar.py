import logging
from datetime import datetime, date, timedelta
from typing import Union

log = logging.getLogger(__name__)

def schedule_workout(client, workout_id: str, workout_date: Union[str, date]):
    """Schedule a workout on the Garmin calendar."""
    if isinstance(workout_date, date):
        workout_date = workout_date.isoformat()
    log.info(f"Scheduling workout {workout_id} on {workout_date}")
    return client.schedule_workout(workout_id, workout_date)

def clear_calendar_range(client, start_date: Union[str, date], end_date: Union[str, date]):
    """
    Fetch all scheduled workouts between start_date and end_date (inclusive)
    and unschedule them.
    
    Safeguard: Skips any items containing an atpPlanId (Auto Training Plan) 
    as these cause 403/404 errors.
    """
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    log.info(f"Clearing calendar from {start_date} to {end_date}")

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
    for year, month in months:
        log.debug(f"Fetching calendar for {year}-{month}")
        try:
            cal = client.get_scheduled_workouts(year, month)
            if cal and "calendarItems" in cal:
                all_items.extend(cal["calendarItems"])
        except Exception as e:
            log.error(f"Failed to fetch calendar for {year}-{month}: {e}")

    # Filter by date range and type
    to_unschedule = []
    for item in all_items:
        item_date_str = item.get("date")
        if not item_date_str:
            continue
        
        try:
            item_date = datetime.strptime(item_date_str, "%Y-%m-%d").date()
        except ValueError:
            continue

        if start_date <= item_date <= end_date:
            # Safeguard: Skip ATP plans
            if item.get("atpPlanId"):
                log.info(f"Skipping ATP item '{item.get('title')}' on {item_date_str}")
                continue
            
            to_unschedule.append(item)

    if not to_unschedule:
        log.info("No items found to clear in this range.")
        return

    log.info(f"Unscheduling {len(to_unschedule)} items...")
    for item in to_unschedule:
        calendar_item_id = item.get("calendarItemId")
        title = item.get("title")
        item_date = item.get("date")
        log.info(f"Unscheduling: {title} on {item_date} (ID: {calendar_item_id})")
        try:
            client.unschedule_workout(calendar_item_id)
        except Exception as e:
            log.error(f"Failed to unschedule item {calendar_item_id}: {e}")
