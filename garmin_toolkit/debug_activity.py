import sys
import logging
import json
from garmin_training_toolkit_sdk.utils import get_authenticated_client, find_token_file

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

def deep_search_keys(activity_id):
    token_file = find_token_file()
    client = get_authenticated_client(token_file)
    
    log.info(f"Deep searching all keys for activity: {activity_id}")
    details = client.get_activity_details(activity_id)
    
    # 1. Search in Descriptors
    descriptors = details.get("metricDescriptors", [])
    all_descriptor_keys = [d["key"] for d in descriptors]
    
    # 2. Search for ANY key in the whole JSON that contains 'walk' or 'run'
    def find_matches(obj, pattern, found_keys):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if pattern.lower() in str(k).lower():
                    found_keys.add(k)
                find_matches(v, pattern, found_keys)
        elif isinstance(obj, list):
            for item in obj:
                find_matches(item, pattern, found_keys)

    matches = set()
    find_matches(details, "walk", matches)
    find_matches(details, "run", matches)

    print("\n" + "="*60)
    print(f"DEEP KEY SEARCH FOR ACTIVITY: {activity_id}")
    print("="*60)
    
    print("\nMATCHING KEYS FOUND IN RAW RESPONSE:")
    for m in sorted(matches):
        print(f" - {m}")

    print("\nALL METRIC DESCRIPTOR KEYS:")
    for k in sorted(all_descriptor_keys):
        print(f" - {k}")

    # 3. Look at the first metric row to see its length
    raw_metrics = details.get("activityDetailMetrics", [])
    if raw_metrics:
        first_row = raw_metrics[0].get("metrics", [])
        print(f"\nTelemetry Row Length: {len(first_row)} columns")
        print(f"Number of Descriptors: {len(descriptors)}")
        
        if len(first_row) > len(descriptors):
            print("\nWARNING: Found more data columns than descriptors! Garmin is hiding something.")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python debug_activity.py <ACTIVITY_ID>")
    else:
        deep_search_keys(sys.argv[1])
