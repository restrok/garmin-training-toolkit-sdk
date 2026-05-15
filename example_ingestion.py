"""Example script demonstrating data ingestion using the Garmin Training Toolkit SDK."""

import json
import logging
from datetime import datetime, timedelta

from garmin_training_toolkit_sdk.extractors import (
    get_activities,
    get_activity_telemetry,
    get_hrv_data,
    get_readiness_data,
)
from garmin_training_toolkit_sdk.utils import find_token_file, get_authenticated_client

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    """Main execution function for example ingestion."""
    log.info("Starting example data ingestion using the new garmin_training_toolkit_sdk SDK")

    token_file = find_token_file()
    if not token_file:
        log.error("Not authenticated. Run authentication first.")
        return

    try:
        client = get_authenticated_client(token_file)
        log.info("Connected to Garmin Connect.")
    except Exception as e:
        log.error("Failed to connect: %s", e)
        return

    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    log.info("Fetching data from %s to %s...", start_str, end_str)

    # Fetch Data using the SDK and Pydantic models
    activities = get_activities(client, start_str, end_str)
    hrv = get_hrv_data(client, start_str, end_str)
    readiness = get_readiness_data(client, end_str)

    log.info("Retrieved %d activities.", len(activities))
    log.info("Retrieved %d HRV records.", len(hrv))
    log.info("Retrieved %d readiness records.", len(readiness))

    # 2. Detail Extraction (Telemetry) for the most recent activity
    if activities:
        latest_activity_id = activities[0].id
        log.info("\nFetching detailed telemetry for latest activity (%s)...", latest_activity_id)
        telemetry = get_activity_telemetry(client, latest_activity_id)
        log.info("Retrieved %d telemetry ticks.", telemetry.metric_count)

        if telemetry.ticks:
            log.info("\nSample Telemetry Point (Tick 1):")
            print(json.dumps(telemetry.ticks[0].model_dump(), indent=2, default=str))

        log.info("\nSample Activity Summary (Pydantic Model to JSON):")
        print(json.dumps(activities[0].model_dump(), indent=2, default=str))

    log.info("\nIngestion test complete. Data is ready for the external AI pipeline.")


if __name__ == "__main__":
    main()
