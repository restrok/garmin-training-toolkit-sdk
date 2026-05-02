from datetime import date, timedelta
from garmin_training_toolkit_sdk.core.garmin import GarminProvider
import json

def debug_swim():
    print("Initializing GarminProvider...")
    try:
        provider = GarminProvider()
        
        # Fetch activities for the last 2 days
        today = date.today()
        start_date = today - timedelta(days=2)
        
        print(f"Fetching activities from {start_date} to {today}...")
        raw_list = provider.client.get_activities_by_date(start_date.isoformat(), today.isoformat())
        
        swim_raw = next((a for a in raw_list if "test-swim" in a.get("activityName", "").lower() or a.get("activityType", {}).get("typeKey") == "lap_swimming"), None)
        
        if swim_raw:
            print("\n🔍 Raw Activity Data (Full):")
            print(json.dumps(swim_raw, indent=2))
            
            # Now run the SDK object version
            activities = provider.get_activities(start_date, today)
            swim_activity = next((a for a in activities if "test-swim" in a.name.lower() or a.type == "lap_swimming"), None)
        
        if swim_activity:
            print("\n✅ Found Swim Activity!")
            print(f"Name: {swim_activity.name}")
            print(f"Type: {swim_activity.type}")
            print(f"Date: {swim_activity.date}")
            print("-" * 20)
            print(f"Pool Length: {swim_activity.pool_length_m}m")
            print(f"Total Strokes: {swim_activity.total_strokes}")
            print(f"Avg SWOLF: {swim_activity.avg_swolf}")
            print(f"Distance: {swim_activity.distance_m}m")
            print(f"Duration: {swim_activity.duration_sec}s")
            
            # Try to get splits if available
            print("\nFetching splits...")
            from garmin_training_toolkit_sdk.extractors.activities import get_activity_splits
            splits = get_activity_splits(provider.client, swim_activity.id)
            if splits:
                print(f"Found {len(splits)} splits/laps:")
                for s in splits[:3]: # Show first 3
                    print(f"  Lap {s.index}: {s.distance_m}m | Strokes: {s.strokes} | SWOLF: {s.avg_swolf}")
            else:
                print("No splits found.")
                
        else:
            print("\n❌ Could not find 'test-swim' activity.")
            print("Found these activities:")
            for a in activities:
                print(f"  - {a.name} ({a.type})")
                
    except Exception as e:
        print(f"\n💥 Error: {e}")

if __name__ == "__main__":
    debug_swim()
