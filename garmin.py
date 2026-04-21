#!/usr/bin/env python3
"""
Garmin Training System CLI
Unified command interface using local data files.
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
log = logging.getLogger(__name__)

REPORT_FILE = Path(__file__).parent / "garmin-analyzer" / "data" / "garmin_report.json"
WORKOUTS_FILE = Path(__file__).parent / "garmin-workout-uploader" / "workouts.json"


def format_duration(seconds: float) -> str:
    """Format seconds to hh:mm:ss or mm:ss depending on duration."""
    total_sec = int(seconds)
    if total_sec >= 3600:
        return f"{total_sec//3600}:{(total_sec%3600)//60:02d}:{total_sec%60:02d}"
    return f"{total_sec//60}:{total_sec%60:02d}"


def load_report() -> dict:
    """Load Garmin report data."""
    if not REPORT_FILE.exists():
        log.error(f"Run collector first: {REPORT_FILE}")
        return {}
    with open(REPORT_FILE) as f:
        return json.load(f)


def cmd_collect(args):
    """Run data collector with auto-auth refresh."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from garmin_utils import find_token_file, get_authenticated_client
    
    token_file = find_token_file()
    if not token_file:
        print("Not authenticated. Running auth...")
        subprocess.run(["python3", str(Path(__file__).parent / "garmin.py"), "auth"], check=True)
        token_file = find_token_file()
    
    try:
        client = get_authenticated_client()
        client.get_user_profile()
    except Exception as e:
        if "401" in str(e) or "Unauthorized" in str(e) or "not set" in str(e).lower():
            print("Session expired. Re-authenticating...")
            subprocess.run(["python3", str(Path(__file__).parent / "garmin.py"), "auth"], check=True)
            client = get_authenticated_client()
    
    sys.path.insert(0, str(Path(__file__).parent / "garmin-analyzer"))
    from collector import main as collect_main
    collect_main()


def cmd_progress(args):
    """Show progress tracking."""
    data = load_report()
    if not data:
        return
    
    activities = data.get("activities", [])
    running = [a for a in activities if a.get("type") == "running"]
    
    days = args.days
    total_runs = len(running)
    total_dist = sum(a.get("distance_m", 0) for a in running) / 1000
    total_time = sum(a.get("duration_sec", 0) for a in running) / 3600
    
    hr_values = [a.get("avg_hr", 0) for a in running if a.get("avg_hr")]
    avg_hr = sum(hr_values) / len(hr_values) if hr_values else 0
    
    pace_values = [a.get("avg_pace", 0) for a in running if a.get("avg_pace") and a.get("avg_pace") > 0]
    if pace_values:
        avg_pace = sum(1000 / p for p in pace_values) / len(pace_values)
        pace_str = f"{int(avg_pace//60)}:{int(avg_pace%60):02d}/km"
    else:
        pace_str = "N/A"
    
    vo2 = running[0].get("vo2max") if running else None
    
    print(f"\n{'='*50}")
    print(f"PROGRESS REPORT - Last {days} days")
    print(f"{'='*50}")
    
    print("\n📊 Running")
    print(f"  Runs: {total_runs}")
    print(f"  Distance: {total_dist:.0f} km")
    print(f"  Time: {total_time:.1f} hrs")
    print(f"  Weekly: {total_runs/(days/7):.1f} runs, {total_dist/(days/7):.0f} km")
    if avg_hr:
        print(f"  Avg HR: {avg_hr:.0f} bpm")
    print(f"  Avg pace: {pace_str}")
    if vo2:
        print(f"  VO2max: {vo2}")
    print(f"\n{'='*50}")


def cmd_zones(args):
    """Show HR zones calculated from training data."""
    import argparse
    from datetime import datetime, timedelta
    from garmin_utils import find_token_file, get_authenticated_client
    
    n_activities = getattr(args, 'activities', 5) or 5
    
    data = load_report()
    if not data:
        return
    
    activities = data.get("activities", [])
    running = [a for a in activities if a.get("type") == "running"]
    
    if not running:
        print("No running activities found.")
        return
    
    print(f"\n{'='*50}")
    print(f"HR ZONES ANALYSIS")
    print(f"{'='*50}")
    
    try:
        token_file = find_token_file()
        if not token_file:
            print("Not authenticated. Run garmin.py auth first.")
            return
        client = get_authenticated_client(token_file)
    except Exception as e:
        print(f"Could not authenticate: {e}")
        return
    
    # Get max HR from last 6 months (all activities)
    print("\n📊 MAX HR (last 6 months):")
    try:
        start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        all_activities = client.get_activities_by_date(start_date, end_date)
        
        max_hrs = []
        for a in all_activities:
            max_hr = a.get('maxHR')
            if max_hr:
                max_hrs.append(int(max_hr))
        
        if max_hrs:
            max_hrs_sorted = sorted(max_hrs, reverse=True)
            avg_top3 = sum(max_hrs_sorted[:3]) / 3
            print(f"  Top 3 avg: {int(avg_top3)} bpm")
            print(f"  Max recorded: {max(max_hrs)} bpm")
            max_hr_display = int(avg_top3)
        else:
            max_hr_display = 192
            print(f"  Using default: {max_hr_display} bpm")
    except Exception as e:
        max_hr_display = 192
        print(f"  Could not fetch: using {max_hr_display} bpm")
    
    # Get resting HR from HRV data
    print("\n💓 RESTING HR:")
    try:
        hrv_data = client.get_hrv_data(end_date)
        if hrv_data and isinstance(hrv_data, list):
            # Get recent HRV readings and estimate resting HR
            rhr_vals = []
            for h in hrv_data[:30]:  # Last 30 days
                avg_hrv = h.get('averageHRV')
                if avg_hrv:
                    # Rough estimate: lower HRV = higher resting HR
                    # This is approximate, better to use actual RHR if available
                    pass
            # Try to get resting HR from stress data
            stress = client.get_stress_data(end_date)
            if stress and isinstance(stress, list):
                for s in stress[:7]:  # Last 7 days
                    rhr = s.get('restingHeartRate')
                    if rhr:
                        rhr_vals.append(int(rhr))
            if rhr_vals:
                avg_rhr = sum(rhr_vals) / len(rhr_vals)
                print(f"  Avg (last 7 days): {int(avg_rhr)} bpm")
                rhr_display = int(avg_rhr)
            else:
                rhr_display = 70
                print(f"  Using estimate: {rhr_display} bpm")
        else:
            rhr_display = 70
            print(f"  Using default: {rhr_display} bpm")
    except Exception as e:
        rhr_display = 70
        print(f"  Could not fetch: using {rhr_display} bpm")
    
    print(f"\n🏃 HR vs PACE (last {n_activities} activities):")
    
    all_zones = {1: [], 2: [], 3: [], 4: [], 5: []}
    used_activities = 0
    
    for i, activity in enumerate(running[:n_activities]):
        activity_id = activity.get("id")
        name = activity.get("name", "Unknown")
        
        try:
            details = client.get_activity_details(str(activity_id))
            
            # Find metric indices
            hr_idx = speed_idx = None
            for d in details.get("metricDescriptors", []):
                if d.get("key") == "directHeartRate":
                    hr_idx = d["metricsIndex"]
                if d.get("key") == "directSpeed":
                    speed_idx = d["metricsIndex"]
            
            if hr_idx is None or speed_idx is None:
                continue
            
            # Extract HR and speed pairs
            hr_speeds = []
            for m in details.get("activityDetailMetrics", []):
                hr = m["metrics"][hr_idx]
                speed = m["metrics"][speed_idx]
                if hr and speed and speed > 0:
                    hr_speeds.append((int(hr), speed))
            
            if not hr_speeds:
                continue
            
            # Calculate percentiles for this activity
            hr_vals = [h for h, _ in hr_speeds]
            p50 = sorted(hr_vals)[len(hr_vals) // 2]
            max_hr = max(hr_vals)
            
            # Define zones based on this activity's data
            # Z1: <120 (warmup/walk)
            # Z2: 120-p50 (easy)
            # Z3: p50-(p50+10) (tempo)
            # Z4: (p50+10)-max-10
            # Z5: >max-10
            zones = {"Z1": [], "Z2": [], "Z3": [], "Z4": [], "Z5": []}
            for hr, speed in hr_speeds:
                if hr < 120:
                    zones["Z1"].append(speed)
                elif hr < p50:
                    zones["Z2"].append(speed)
                elif hr < p50 + 10:
                    zones["Z3"].append(speed)
                elif hr < max_hr - 10:
                    zones["Z4"].append(speed)
                else:
                    zones["Z5"].append(speed)
            
            print(f"\n{name}:")
            for z, speeds in zones.items():
                if speeds:
                    avg_mps = sum(speeds) / len(speeds)
                    sec_per_km = 1000 / avg_mps
                    min_pace = int(sec_per_km // 60)
                    sec_pace = int(sec_per_km % 60)
                    print(f"   {z}: {min_pace}:{sec_pace:02d}/km ({len(speeds)} pts)")
                    all_zones[int(z.replace("Z", ""))].extend(speeds)
            
            used_activities += 1
            
        except Exception as e:
            print(f"   Error getting details: {e}")
            continue
    
    if not any(all_zones.values()):
        print("\nNo detailed data available. Run collector to fetch splits.")
        return
    
    print(f"\n{'='*50}")
    print("SUMMARY (ALL ACTIVITIES)")
    print(f"{'='*50}")
    
    # Show summary
    print("\nZone | Pace      | Points")
    print("-" * 35)
    for z in range(1, 6):
        speeds = all_zones[z]
        if speeds:
            avg_mps = sum(speeds) / len(speeds)
            sec_per_km = 1000 / avg_mps
            min_pace = int(sec_per_km // 60)
            sec_pace = int(sec_per_km % 60)
            print(f" Z{z}  | {min_pace}:{sec_pace:02d}/km | {len(speeds)} pts")
        else:
            print(f" Z{z}  | --        | 0 pts")
    
    # Load custom zones from .env if available
    from garmin_utils import load_env_file
    prefs = load_env_file()
    
    hr_z1 = prefs.get("HR_Z1_MAX")
    hr_z2 = prefs.get("HR_Z2_MAX")
    hr_z3 = prefs.get("HR_Z3_MAX")
    hr_z4 = prefs.get("HR_Z4_MAX")
    
    if hr_z1 and hr_z2 and hr_z3 and hr_z4:
        print(f"\n{'='*50}")
        print("CUSTOM ZONES (from .env)")
        print(f"{'='*50}")
        print(f"  Z1: <{hr_z1}")
        print(f"  Z2: {int(hr_z1)+1}-{hr_z2}")
        print(f"  Z3: {int(hr_z2)+1}-{hr_z3}")
        print(f"  Z4: {int(hr_z3)+1}-{hr_z4}")
        print(f"  Z5: >{hr_z4}")
    
    print(f"\n{'='*50}")


def cmd_recovery(args):
    """Analyze recovery status."""
    data = load_report()
    if not data:
        return
    
    print(f"\n{'='*50}")
    print("RECOVERY ANALYSIS")
    print(f"{'='*50}")
    
    hrv = data.get("hrv", [])
    if hrv:
        vals = [h.get("avg_hrv", 0) for h in hrv if h.get("avg_hrv")]
        if vals:
            print(f"\n💓 HRV: {sum(vals)/len(vals):.0f} ms avg")
            print(f"  Latest: {vals[-1]} ms")
    else:
        print("\n💓 No HRV data")
    
    readiness = data.get("training_readiness", [])
    if readiness:
        vals = [r.get("value", 0) for r in readiness if r.get("value")]
        if vals:
            print(f"\n📈 Readiness: {sum(vals)/len(vals):.0f}/100")
    else:
        print("\n📈 No readiness data")
    
    print(f"\n{'='*50}")


def cmd_predict(args):
    """Predict race times."""
    data = load_report()
    if not data:
        return
    
    print(f"\n{'='*50}")
    print("RACE PREDICTIONS")
    print(f"{'='*50}")
    
    races = data.get("race_predictions", {})
    if races:
        print("Garmin:")
        for race, sec in [("5K", races.get("raceTime5K")), ("10K", races.get("raceTime10K")),
                          ("Half", races.get("raceTimeHalf")), ("Marathon", races.get("raceTimeMarathon"))]:
            if sec:
                print(f"  {race}: {format_duration(sec)}")
    
    activities = data.get("activities", [])
    running = [a for a in activities if a.get("type") == "running" and a.get("avg_pace")]
    
    if running:
        results = []
        for a in running:
            pace = a.get("avg_pace", 0)
            distance = a.get("distance_m", 0) / 1000
            if pace > 0 and distance >= 5:
                sec_km = 1000 / pace
                results.append({
                    "pace": sec_km,
                    "distance": distance,
                })
        
        if results:
            # Use median of best 3 runs
            results.sort(key=lambda x: x["pace"])
            best_3 = results[:3]
            median_pace = sorted([r["pace"] for r in best_3])[1]
            
            # Riegel: T2 = T1 * (D2/D1)^1.06
            baseline_dist = 10  # baseline is 10K
            baseline_time = median_pace * baseline_dist
            
            distances = {"5K": 5, "10K": 10, "Half": 21.1, "Marathon": 42.2}
            
            print("\n📈 Realistic (Riegel formula, median best 3):")
            for race, dist in distances.items():
                pred_time = baseline_time * (dist / baseline_dist) ** 1.06
                print(f"  {race}: {format_duration(pred_time)}")
    
    print(f"\n{'='*50}")


def cmd_export(args):
    """Export comprehensive training status report."""
    data = load_report()
    if not data:
        print("No data. Run: python3 garmin.py collect")
        return
    
    activities = data.get("activities", [])
    running = [a for a in activities if a.get("type") == "running"]
    
    # Basic stats
    total_runs = len(running)
    total_dist = sum(a.get("distance_m", 0) for a in running) / 1000
    total_time = sum(a.get("duration_sec", 0) for a in running) / 3600
    
    hr_values = [a.get("avg_hr", 0) for a in running if a.get("avg_hr")]
    avg_hr = sum(hr_values) / len(hr_values) if hr_values else 0
    
    pace_values = [a.get("avg_pace", 0) for a in running if a.get("avg_pace") and a.get("avg_pace") > 0]
    avg_pace = sum(1000 / p for p in pace_values) / len(pace_values) if pace_values else 0
    
    vo2 = running[0].get("vo2max") if running else None
    
    # HR Zones
    hrs_sorted = sorted(hr_values) if hr_values else []
    if hrs_sorted and len(hrs_sorted) >= 5:
        n = len(hrs_sorted)
        p25 = hrs_sorted[n // 4]
        p75 = hrs_sorted[3 * n // 4]
        max_hr = max(a.get("max_hr", 0) for a in running if a.get("max_hr")) or max(hr_values) + 20
    else:
        p25, p75, max_hr = 153, 165, 193
    
    # Predictions
    race_preds = {}
    if running and pace_values:
        results = []
        for a in running:
            pace = a.get("avg_pace", 0)
            distance = a.get("distance_m", 0) / 1000
            if pace > 0 and distance >= 5:
                sec_km = 1000 / pace
                results.append({"pace": sec_km, "distance": distance})
        
        if results:
            results.sort(key=lambda x: x["pace"])
            best_3 = results[:3]
            median_pace = sorted([r["pace"] for r in best_3])[1]
            baseline_time = median_pace * 10
            for race, dist in [("5K", 5), ("10K", 10), ("Half", 21.1), ("Marathon", 42.2)]:
                pred = baseline_time * (dist / 10) ** 1.06
                race_preds[race] = pred
    
    # Current plan
    plan_info = {}
    if WORKOUTS_FILE.exists():
        with open(WORKOUTS_FILE) as f:
            plan = json.load(f)
        dates = [w.get("date") for w in plan]
        types = {"Easy": 0, "Tempo": 0, "Interval": 0, "Long": 0, "Race": 0}
        for w in plan:
            name = w.get("name", "")
            if "Easy" in name or "Recovery" in name:
                types["Easy"] += 1
            elif "Tempo" in name:
                types["Tempo"] += 1
            elif "Interval" in name:
                types["Interval"] += 1
            elif "Long" in name:
                types["Long"] += 1
            elif "RACE" in name or "Race" in name:
                types["Race"] += 1
        plan_info = {"runs": len(plan), "dates": dates, "types": types}
    
    # Build output
    lines = []
    lines.append("# 🏃 TRAINING STATUS REPORT")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    
    lines.append("## 📊 Training Stats (Last 90 days)")
    lines.append(f"- Runs: {total_runs}")
    lines.append(f"- Distance: {total_dist:.0f} km")
    lines.append(f"- Time: {total_time:.1f} hrs")
    lines.append(f"- Weekly: {total_runs/13:.1f} runs, {total_dist/13:.0f} km")
    if avg_hr:
        lines.append(f"- Avg HR: {avg_hr:.0f} bpm")
    if avg_pace:
        lines.append(f"- Avg pace: {int(avg_pace//60)}:{int(avg_pace%60):02d}/km")
    if vo2:
        lines.append(f"- VO2max: {vo2}")
    lines.append("")
    
    lines.append("## ❤️ HR Zones (Data-Driven)")
    lines.append(f"- Z1: <{int(p25-5)} bpm")
    lines.append(f"- Z2: {int(p25-5)}-{int(p25+5)} bpm (easy)")
    lines.append(f"- Z3: {int(p25+6)}-{int(p75)} bpm (tempo)")
    lines.append(f"- Z4: {int(p75+1)}-{int(max_hr-20)} bpm (threshold)")
    lines.append(f"- Z5: >{int(max_hr-20)} bpm (max)")
    lines.append("")
    
    lines.append("## 🎯 Race Predictions")
    if race_preds:
        for race, sec in race_preds.items():
            lines.append(f"- {race}: {format_duration(sec)}")
    else:
        lines.append("- No data")
    lines.append("")
    
    lines.append("## 📋 Current Plan")
    if plan_info:
        lines.append(f"- Workouts: {plan_info['runs']}")
        if plan_info.get("dates"):
            lines.append(f"- Period: {min(plan_info['dates'])} to {max(plan_info['dates'])}")
        lines.append(f"- Types: Easy {plan_info['types']['Easy']}, Long {plan_info['types']['Long']}, Tempo {plan_info['types']['Tempo']}, Intervals {plan_info['types']['Interval']}")
    else:
        lines.append("- No plan loaded")
    lines.append("")
    
    lines.append("## 🏆 Best Times")
    if running:
        results = []
        for a in running:
            pace = a.get("avg_pace", 0)
            if pace > 0:
                sec_km = 1000 / pace
                results.append({"date": a.get("date", "")[:10], "pace": sec_km})
        results.sort(key=lambda x: x["pace"])
        for i, r in enumerate(results[:5], 1):
            lines.append(f"- #{i} {r['date']}: {int(r['pace']//60)}:{int(r['pace']%60):02d}/km")
    
    output = "\n".join(lines)
    
    if args.file:
        Path(args.file).write_text(output)
        print(f"Exported to: {args.file}")
    else:
        print(output)


def cmd_best(args):
    """Show best race times."""
    data = load_report()
    if not data:
        return
    
    activities = data.get("activities", [])
    running = [a for a in activities if a.get("type") == "running" and a.get("avg_pace")]
    
    if not running:
        print("No running activities with pace data found.")
        return
    
    results = []
    for a in running:
        pace = a.get("avg_pace", 0)
        if pace > 0:
            sec_km = 1000 / pace
            time_10k = sec_km * 10
            results.append({
                "date": a.get("date", "")[:10],
                "name": a.get("name", "Running")[:30],
                "distance": a.get("distance_m", 0) / 1000,
                "pace": sec_km,
                "time_10k": time_10k,
                "hr": a.get("avg_hr"),
            })
    
    results.sort(key=lambda x: x["time_10k"])
    
    distance = args.distance if args.distance else "10k"
    
    print(f"\n{'='*55}")
    print(f"🏆 YOUR BEST {distance.upper()} TIMES")
    print(f"{'='*55}")
    print(f"{'#':<3} {'Date':<12} {'Dist':<8} {'Pace':<10} {'Time':<10} {'HR':<5}")
    print("-" * 55)
    
    limit = args.limit if args.limit else 5
    
    for i, r in enumerate(results[:limit], 1):
        pace_str = f"{int(r['pace']//60)}:{int(r['pace']%60):02d}/km"
        
        if distance == "10k":
            time_val = r["time_10k"]
        else:
            time_val = r["pace"] * ({"5k": 5, "10k": 10, "half": 21.1, "marathon": 42.2}.get(distance, 10))
        
        time_str = format_duration(time_val)
        hr = int(r["hr"]) if r["hr"] else "-"
        print(f"{i:<3} {r['date']:<12} {r['distance']:.1f}km   {pace_str:<10} {time_str:<10} {hr}")
    
    print(f"{'='*55}")


def cmd_compare(args):
    """Compare current plan vs training data."""
    data = load_report()
    if not data:
        return
    
    if not WORKOUTS_FILE.exists():
        log.error(f"No workouts file: {WORKOUTS_FILE}")
        return
    
    with open(WORKOUTS_FILE) as f:
        current_plan = json.load(f)
    
    activities = [a for a in data.get("activities", []) if a.get("type") == "running"]
    max_hr = max(a.get("max_hr", 0) for a in activities if a.get("max_hr")) or 193
    
    print(f"\n{'='*60}")
    print("PLAN COMPARISON")
    print(f"{'='*60}")
    
    types = {"Easy": 0, "Tempo": 0, "Interval": 0, "Long": 0, "Race": 0}
    for w in current_plan:
        name = w.get("name", "")
        if "Easy" in name or "Recovery" in name:
            types["Easy"] += 1
        elif "Tempo" in name:
            types["Tempo"] += 1
        elif "Interval" in name:
            types["Interval"] += 1
        elif "Long" in name:
            types["Long"] += 1
        elif "RACE" in name or "Race" in name:
            types["Race"] += 1
    
    dates = [w.get("date") for w in current_plan]
    weeks = (datetime.strptime(max(dates), "%Y-%m-%d") - datetime.strptime(min(dates), "%Y-%m-%d")).days // 7 + 1
    
    print(f"\n📋 Current Plan ({min(dates)} to {max(dates)})")
    print(f"  Runs: {len(current_plan)}, Weeks: {weeks}")
    for t, c in types.items():
        if c:
            print(f"  {t}: {c}")
    
    hr_values = [a.get("avg_hr", 0) for a in activities if a.get("avg_hr")]
    if hr_values:
        avg_hr = sum(hr_values) / len(hr_values)
        zone4_pct = sum(1 for hr in hr_values if hr / max_hr * 100 > 80) / len(hr_values) * 100
        
        print("\n⚠️  Training Issue:")
        print(f"  Avg HR: {avg_hr:.0f} bpm ({avg_hr/max_hr*100:.0f}% max)")
        print(f"  Zone 4: {zone4_pct:.0f}% (target: ~20%)")
    
    print(f"\n{'='*60}")


def cmd_plan(args):
    """Generate new plan."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent / "garmin-analyzer"))
    
    use_weather = getattr(args, 'weather', False) or getattr(args, 'use_weather', False)
    
    if use_weather:
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from weather import get_month_summary
            env_file = Path(__file__).parent / ".env"
            env = {}
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if "=" in line:
                        k, v = line.split("=", 1)
                        env[k.strip()] = v.strip()
            race_date = getattr(args, 'race_date', None) or env.get("GOAL_DATE")
            if race_date:
                summary = get_month_summary(race_date)
                if summary:
                    print(f"Weather: {summary['month']} avg {summary['avg_temp']:.1f}°C, max {summary['max_temp']:.1f}°C")
                    if summary.get("avg_temp", 0) > 28:
                        print("→ Hot conditions! Adjusting for heat adaptation")
        except Exception as e:
            print(f"  Warning: Weather not available: {e}")
    
    from plan_generator import main as gen_main
    gen_main()


def cmd_auth(args):
    """Run browser authentication."""
    import sys
    # Save current argv, pass empty to avoid conflict
    original_argv = sys.argv
    
    # Build auth args
    auth_args = []
    if getattr(args, 'email', None):
        auth_args.extend(["--email", args.email])
    if getattr(args, 'password', None):
        auth_args.extend(["--password", args.password])
    if getattr(args, 'headless', None):
        auth_args.append("--headless")
    auth_args.extend(getattr(args, 'auth_args', []) or [])
    
    sys.argv = ['garmin_auth'] + auth_args
    sys.path.insert(0, str(Path(__file__).parent))
    from garmin_auth import main as auth_main
    try:
        auth_main()
    finally:
        sys.argv = original_argv


def cmd_upload(args):
    """Upload workouts to Garmin."""
    import sys
    import subprocess
    from pathlib import Path
    
    sys.path.insert(0, str(Path(__file__).parent))
    from garmin_utils import find_token_file, get_authenticated_client
    
    token_file = find_token_file()
    if not token_file:
        print("Not authenticated. Running auth...")
        subprocess.run(["python3", str(Path(__file__).parent / "garmin.py"), "auth"], check=True)
        token_file = find_token_file()
    
    try:
        get_authenticated_client()
    except Exception as e:
        if "401" in str(e) or "Unauthorized" in str(e):
            print("Session expired. Re-authenticating...")
            subprocess.run(["python3", str(Path(__file__).parent / "garmin.py"), "auth"], check=True)
            get_authenticated_client()
        else:
            raise
    
    # Pass args to uploader
    sys.argv = ["garmin_workout_uploader.py"]
    if args.file:
        sys.argv.extend(["--file", args.file])
    if args.clean_all:
        sys.argv.append("--clean-all")
    elif args.clean:
        if args.clean == "all":
            sys.argv.append("--clean-all")
        else:
            sys.argv.extend(["--clean", args.clean])
    sys.argv.append("--yes")
    
    sys.path.insert(0, str(Path(__file__).parent / "garmin-workout-uploader"))
    from garmin_workout_uploader import main as upload_main
    upload_main()


def cmd_setup(args):
    """Setup wizard for Garmin toolkit."""
    from pathlib import Path
    PROJECT_ROOT = Path(__file__).parent
    ENV_FILE = PROJECT_ROOT / ".env"
    
    GOAL_RACES = ["5K", "10K", "half marathon", "marathon"]
    DEFAULTS = {
        "10K": {"days": 3, "max_session": 90, "easy": "6:00", "tempo": "5:30", "interval": "5:15"},
        "5K": {"days": 3, "max_session": 60, "easy": "6:15", "tempo": "5:45", "interval": "5:00"},
        "half": {"days": 4, "max_session": 120, "easy": "6:00", "tempo": "5:30", "interval": "5:15"},
        "marathon": {"days": 5, "max_session": 150, "easy": "6:00", "tempo": "5:30", "interval": "5:15"},
    }
    
    def load_env():
        env = {}
        if ENV_FILE.exists():
            with open(ENV_FILE) as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        env[k.strip()] = v.strip()
        return env
    
    def save_env(env):
        lines = [f"{k}={v}" for k, v in env.items() if v]
        ENV_FILE.write_text("\n".join(lines) + "\n")
    
    def ask(prompt, default=None):
        d = f" [{default}]" if default else ""
        return input(f"{prompt}{d}: ").strip() or (default or "")
    
    env = load_env()
    
    if args.show:
        print("\n=== Current Configuration ===")
        for key in ["GOAL_RACE", "GOAL_DATE", "GOAL_TIME", "RACE_PACE_TARGET", "TRAINING_DAYS", 
                    "MAX_SESSION_MINUTES", "WEATHER_CITY", "EASY_PACE", "TEMPO_PACE", "INTERVAL_PACE"]:
            print(f"  {key}: {env.get(key, '(not set)')}")
        return
    
    if args.section == "goals":
        race = ask("Goal race", env.get("GOAL_RACE", "10K"))
        env["GOAL_RACE"] = race.upper()
        env["GOAL_DATE"] = ask("Race date (YYYY-MM-DD)", env.get("GOAL_DATE"))
        env["GOAL_TIME"] = ask("Goal time (HH:MM or MM:SS)", env.get("GOAL_TIME"))
        env["RACE_PACE_TARGET"] = ask("Target pace (if no goal time)", env.get("RACE_PACE_TARGET"))
        save_env(env)
        print("✓ Goals updated")
        return
    
    if args.section == "profile":
        env["TRAINING_DAYS"] = ask("Days per week", env.get("TRAINING_DAYS"))
        env["MAX_SESSION_MINUTES"] = ask("Max session (min)", env.get("MAX_SESSION_MINUTES"))
        save_env(env)
        print("✓ Profile updated")
        return
    
    if args.section == "paces":
        env["EASY_PACE"] = ask("Easy pace (MM:SS)", env.get("EASY_PACE", "6:00"))
        env["TEMPO_PACE"] = ask("Tempo pace", env.get("TEMPO_PACE", "5:30"))
        env["INTERVAL_PACE"] = ask("Interval pace", env.get("INTERVAL_PACE", "5:15"))
        save_env(env)
        print("✓ Paces updated")
        return
    
    # Full interactive setup
    print("\n=== Garmin Toolkit Setup ===\n")
    print(f"Options: {', '.join(GOAL_RACES)}")
    race = ask("Goal race", env.get("GOAL_RACE", "10K")).upper()
    if race not in GOAL_RACES:
        race = "10K"
    env["GOAL_RACE"] = race
    env["GOAL_DATE"] = ask("Race date (YYYY-MM-DD)", env.get("GOAL_DATE"))
    env["GOAL_TIME"] = ask("Goal time (HH:MM or MM:SS)", env.get("GOAL_TIME"))
    env["RACE_PACE_TARGET"] = ask("Target pace (if no goal time)", env.get("RACE_PACE_TARGET"))
    env["TRAINING_DAYS"] = ask("Days/week", env.get("TRAINING_DAYS", DEFAULTS.get(race.lower(), DEFAULTS["10K"])["days"]))
    env["MAX_SESSION_MINUTES"] = ask("Max session (min)", env.get("MAX_SESSION_MINUTES", DEFAULTS.get(race.lower(), DEFAULTS["10K"])["max_session"]))
    env["WEATHER_CITY"] = ask("Weather city", env.get("WEATHER_CITY"))
    env["EASY_PACE"] = ask("Easy pace", env.get("EASY_PACE", DEFAULTS.get(race.lower(), DEFAULTS["10K"])["easy"]))
    env["TEMPO_PACE"] = ask("Tempo pace", env.get("TEMPO_PACE", DEFAULTS.get(race.lower(), DEFAULTS["10K"])["tempo"]))
    env["INTERVAL_PACE"] = ask("Interval pace", env.get("INTERVAL_PACE", DEFAULTS.get(race.lower(), DEFAULTS["10K"])["interval"]))
    save_env(env)
    print("\n✓ Configuration saved to .env")
    print("\nNext: python3 garmin.py auth && python3 garmin.py collect")


def cmd_analyze(args):
    """Analyze recent workouts with optional weather and plan comparison."""
    import json
    from datetime import datetime, timedelta
    
    data_file = Path(__file__).parent / "garmin-analyzer" / "data" / "garmin_report.json"
    plan_file = Path(__file__).parent / "garmin-workout-uploader" / "workouts.json"
    
    if not data_file.exists():
        print("Error: No data. Run 'python3 garmin.py collect' first.")
        return 1
    
    with open(data_file) as f:
        data = json.load(f)
    
    # Load plan for comparison
    plan_by_date = {}
    if plan_file.exists():
        with open(plan_file) as f:
            plan = json.load(f)
            plan_by_date = {w.get('date'): w for w in plan if w.get('date')}
    
    # Determine if we need weather - auto-use if available, unless --no-weather specified
    use_weather = not args.no_weather if hasattr(args, 'no_weather') and args.no_weather else True
    if args.weather:
        use_weather = True
    
    # Load weather module if needed
    weather_data = {}
    if use_weather:
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from weather import get_for_date, get_month_summary
            # Pre-fetch weather for dates in range
            cutoff = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
            for a in data.get("activities", []):
                date = a.get("date", "")[:10]
                if date >= cutoff:
                    weather_data[date] = get_for_date(date)
        except Exception as e:
            print(f"  Warning: Weather not available: {e}")
    
    # Filter activities
    cutoff = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
    activities = [a for a in data.get("activities", []) if a.get("date", "") >= cutoff]
    running = [a for a in activities if a.get("type") == "running"]
    
    # If JSON requested, build and return early
    if args.json:
        by_week = {}
        for a in running:
            date = a.get('date', '')
            if date:
                d = datetime.strptime(date[:10], '%Y-%m-%d')
                week = d.strftime('%Y-W%W')
                if week not in by_week:
                    by_week[week] = {'runs': 0, 'dist': 0}
                by_week[week]['dist'] += a.get('distance_m', 0) / 1000
                by_week[week]['runs'] += 1
        
        total_dist = sum(a.get('distance_m', 0) for a in running) / 1000
        total_time = sum(a.get('duration_sec', 0) for a in running) / 3600
        avg_hr = sum(a.get('avg_hr', 0) for a in running if a.get('avg_hr')) / max(1, len([a for a in running if a.get('avg_hr')]))
        in_plan_count = len([a for a in running if a.get('date', '')[:10] in plan_by_date])
        
        output = {
            "period_days": args.days,
            "activities": [],
            "summary": {
                "total_runs": len(running),
                "total_distance_km": round(total_dist, 2),
                "total_time_hours": round(total_time, 2),
                "avg_hr": int(avg_hr),
                "in_plan_count": in_plan_count
            },
            "weekly": by_week,
            "weather": {d: w for d, w in weather_data.items() if w}
        }
        
        for a in running:
            date_full = a.get("date", "")
            date_str = date_full[:10] if date_full else ""
            
            act = {
                "date": date_str,
                "time": date_full[11:] if len(date_full) > 10 else None,
                "distance_km": round(a.get("distance_m", 0) / 1000, 2),
                "duration_min": int(a.get("duration_sec", 0) / 60),
                "avg_hr": a.get("avg_hr"),
                "max_hr": a.get("max_hr"),
                "calories": a.get("calories"),
                "weather": weather_data.get(date_str) if date_str else None,
                "splits": a.get("splits", [])
            }
            output["activities"].append(act)
        
        print(json.dumps(output, indent=2))
        return 0
    
    # Text output starts here
    print("\n" + "=" * 65)
    print(f"         📊 WORKOUT ANALYSIS - Last {args.days} days")
    print("=" * 65)
    
    # Table header
    print(f"\n{'Date':<12} {'Dist':>5} {'Time':>6} {'Pace':>7} {'HR':>6} {'Weather':>8} {'Plan':<6}")
    print("-" * 65)
    
    for a in running[:15]:
        date = a.get("date", "")[:10]
        dist = a.get("distance_m", 0) / 1000
        dur = int(a.get("duration_sec", 0) / 60)
        pace = a.get("avg_pace", 0)
        hr = int(a.get("avg_hr", 0)) if a.get("avg_hr") else 0
        
        # Pace
        if pace:
            sec_km = 1000 / pace if pace > 0 else 0
            pace_str = f"{int(sec_km//60)}:{int(sec_km%60):02d}"
        else:
            pace_str = "-"
        
        # Weather
        w = weather_data.get(date)
        weather = f"{int(w['temp_avg'])}°" if w and w.get('temp_avg') else "-"
        
        # Plan status
        in_plan = "✅" if date in plan_by_date else "-"
        
        print(f"{date:<12} {dist:>4.1f}km {dur:>5}min {pace_str:>7} {hr:>6} {weather:>8} {in_plan:<6}")
    
# Summary
    total_dist = sum(a.get('distance_m', 0) for a in running) / 1000
    total_time = sum(a.get('duration_sec', 0) for a in running) / 3600
    avg_hr = sum(a.get('avg_hr', 0) for a in running if a.get('avg_hr')) / max(1, len([a for a in running if a.get('avg_hr')]))
    in_plan_count = len([a for a in running if a.get('date', '')[:10] in plan_by_date])
    
    print("\n📈 SUMMARY")
    print("-" * 65)
    print(f"  Runs: {len(running)} | Distance: {total_dist:.1f}km | Time: {total_time:.1f}h")
    print(f"  Avg HR: {int(avg_hr)} bpm | In plan: {in_plan_count}/{len(running)}")
    
    # Weekly breakdown - compute before JSON check
    by_week = {}
    for a in running:
        date = a.get('date', '')
        if date:
            d = datetime.strptime(date[:10], '%Y-%m-%d')
            week = d.strftime('%Y-W%W')
            if week not in by_week:
                by_week[week] = {'runs': 0, 'dist': 0}
            by_week[week]['dist'] += a.get('distance_m', 0) / 1000
            by_week[week]['runs'] += 1
    
    # Build JSON output structure
    if args.json:
        output = {
            "period_days": args.days,
            "activities": [],
            "summary": {
                "total_runs": len(running),
                "total_distance_km": total_dist,
                "total_time_hours": total_time,
                "avg_hr": int(avg_hr),
                "in_plan_count": in_plan_count
            },
            "weekly": by_week,
            "weather": {d: w for d, w in weather_data.items() if w}
        }
        
        for a in running:
            act = {
                "date": a.get("date", "")[:10],
                "distance_km": round(a.get("distance_m", 0) / 1000, 2),
                "duration_min": int(a.get("duration_sec", 0) / 60),
                "avg_hr": a.get("avg_hr"),
                "max_hr": a.get("max_hr"),
                "calories": a.get("calories"),
                "splits": a.get("splits", [])
            }
            output["activities"].append(act)
        
        print(json.dumps(output, indent=2))
        return 0

    # Text output
    if by_week:
        print("\n📅 WEEKLY VOLUME")
        print("-" * 65)
        for week in sorted(by_week.keys(), reverse=True)[:4]:
            w = by_week[week]
            print(f"  {week}: {w['runs']} runs, {w['dist']:.1f}km")
    
    # Show detailed splits for last workout if requested
    # Use splits from collected data (WARMUP, ACTIVE, COOLDOWN)
    if args.days <= 7 and running:
        splits = running[0].get('splits', [])
        if splits:
            print("\n🔍 LAST WORKOUT STAGES")
            print("-" * 70)
            for s in splits:
                stype = s.get('type', '?')
                stype_clean = {'WARMUP': '🔥', 'ACTIVE': '🏃', 'COOLDOWN': '❄️', 'RECOVERY': '🔵', 'INTERVAL': '⚡'}.get(stype, '•')
                
                sdist = s.get('distance_m', 0) / 1000
                sdur = s.get('duration_sec', 0)
                mins = int(sdur // 60)
                secs = int(sdur % 60)
                
                pace_mps = s.get('avg_pace_mps', 0)
                if pace_mps > 0:
                    sec_per_km = 1000 / pace_mps
                    sp = f"{int(sec_per_km//60)}:{int(sec_per_km%60):02d}/km"
                else:
                    sp = '-'
                
                shr = int(s.get('avg_hr', 0)) if s.get('avg_hr') else '-'
                
                print(f"  {stype_clean} {stype}")
                print(f"    Distance: {sdist:.2f}km | Time: {mins}m {secs}s | Pace: {sp} | HR: {shr} bpm")
    
    # Race context
    env_file = Path(__file__).parent / ".env"
    env = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    
    race_date = env.get("GOAL_DATE")
    race_type = env.get("GOAL_RACE", "10K")
    
    if race_date and use_weather:
        try:
            ws = get_month_summary(race_date)
            if ws:
                print(f"\n🏃 RACE CONTEXT ({race_type} {race_date})")
                print("-" * 65)
                print(f"  Historical: {ws['avg_temp']:.1f}°C avg, {ws['max_temp']:.1f}°C max")
                if ws['avg_temp'] > 28:
                    print("  ⚠️  Hot conditions expected - consider heat adaptation!")
        except Exception:
            pass
    
    print()
    return 0


def cmd_weather_init(args):
    """Initialize weather module."""
    sys.path.insert(0, str(Path(__file__).parent))
    from weather import init, backfill_last_year
    coords = init(args.city)
    print(f"✓ City: {coords['city']} ({coords['lat']}, {coords['lon']})")
    if args.backfill:
        count = backfill_last_year()
        print(f"✓ Backfilled {count} days")
    print("Weather module ready!")


def cmd_weather_cron(args):
    """Setup weather cron job."""
    import subprocess
    sys.path.insert(0, str(Path(__file__).parent))
    from weather import is_configured
    if not is_configured():
        print("Error: Run 'python3 garmin.py weather init --city <city>' first.")
        return 1
    
    script = Path(__file__).parent / "weather_cron.sh"
    script.write_text(f"""#!/bin/bash
cd {Path(__file__).parent}
python3 -c "from weather import fetch_current; fetch_current()"
""")
    script.chmod(0o755)
    
    cron_line = f"0 * * * * {script}"
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        existing = result.stdout if result.returncode == 0 else ""
    except (FileNotFoundError, OSError):
        existing = ""
    
    if cron_line not in existing:
        subprocess.run(["crontab", "-"], input=existing + "\n" + cron_line, text=True)
        print("✓ Cron job added (hourly)")
    else:
        print("✓ Cron job already exists")
    print(f"Script: {script}")


def cmd_weather_test(args):
    """Test weather fetch."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from weather import get_current, get_summary, is_configured
    if not is_configured():
        print("Error: Run 'python3 garmin.py weather init --city <city>' first.")
        return 1
    current = get_current()
    summary = get_summary()
    print(f"✓ {summary['city']}: {current['temp']}°C ({current['humidity']}% humidity)")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Garmin Training System")
    sub = parser.add_subparsers(dest="command")
    
    sub.add_parser("collect", help="Collect data from Garmin")
    p_auth = sub.add_parser("auth", help="Authenticate with Garmin")
    p_auth.add_argument("--email", "-e", help="Garmin email")
    p_auth.add_argument("--password", "-p", help="Garmin password (or use GARMIN_PASSWORD env)")
    p_auth.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    p_auth.add_argument("auth_args", nargs="*", help="Additional arguments for auth")
    
    p_progress = sub.add_parser("progress", help="Show progress")
    p_progress.add_argument("--days", type=int, default=90)
    
    p_zones = sub.add_parser("zones", help="Show personalized HR zones")
    p_zones.add_argument("--activities", type=int, default=5, help="Number of activities to analyze (default: 5)")
    sub.add_parser("recovery", help="Show recovery status")
    sub.add_parser("predict", help="Race predictions")
    
    p_best = sub.add_parser("best", help="Best race times")
    p_best.add_argument("--distance", default="10k")
    p_best.add_argument("--limit", type=int, default=5)
    
    sub.add_parser("compare", help="Compare plans")
    
    p_export = sub.add_parser("export", help="Export full report")
    p_export.add_argument("--file", help="Save to file")
    
    p_upload = sub.add_parser("upload", help="Upload workouts")
    p_upload.add_argument("--file", help="Workouts file (default: garmin-workout-uploader/workouts.json)")
    p_upload.add_argument("--clean", nargs="?", const="all", help="Delete old workouts (use 'all' to delete everything)")
    p_upload.add_argument("--clean-all", action="store_true", help="Delete ALL old workouts before uploading")
    p_upload.add_argument("--delete", metavar="WORKOUT_ID", help="Delete specific workout by ID")
    
    p_plan = sub.add_parser("plan", help="Generate training plan")
    p_plan.add_argument("--weather", action="store_true", help="Use weather data")
    p_plan.add_argument("--no-weather", action="store_true", help="Skip weather data")
    p_plan.add_argument("--race-date", help="Race date (YYYY-MM-DD)")
    
    p_setup = sub.add_parser("setup", help="Setup wizard")
    p_setup.add_argument("--section", choices=["goals", "profile", "paces"], help="Update specific section")
    p_setup.add_argument("--show", action="store_true", help="Show current config")
    
    p_analyze = sub.add_parser("analyze", help="Analyze workouts")
    p_analyze.add_argument("-d", "--days", type=int, default=30)
    p_analyze.add_argument("--weather", action="store_true", help="Include weather data")
    p_analyze.add_argument("--no-weather", action="store_true", help="Skip weather")
    p_analyze.add_argument("--json", action="store_true", help="Output as JSON")
    
    p_weather = sub.add_parser("weather", help="Weather module")
    p_weather_sub = p_weather.add_subparsers(dest="weather_command")
    p_weather_init = p_weather_sub.add_parser("init", help="Initialize weather")
    p_weather_init.add_argument("--city", required=True)
    p_weather_init.add_argument("--backfill", action="store_true", help="Backfill last year")
    p_weather_sub.add_parser("cron", help="Setup cron")
    p_weather_sub.add_parser("test", help="Test weather")
    
    args = parser.parse_args()
    
    commands = {
        "collect": cmd_collect,
        "progress": cmd_progress,
        "zones": cmd_zones,
        "recovery": cmd_recovery,
        "predict": cmd_predict,
        "best": cmd_best,
        "compare": cmd_compare,
        "export": cmd_export,
        "plan": cmd_plan,
        "auth": cmd_auth,
        "upload": cmd_upload,
        "setup": cmd_setup,
        "analyze": cmd_analyze,
    }
    
    # Handle weather subcommands
    if args.command == "weather":
        if not args.weather_command:
            p_weather.print_help()
        elif args.weather_command == "init":
            cmd_weather_init(args)
        elif args.weather_command == "cron":
            cmd_weather_cron(args)
        elif args.weather_command == "test":
            cmd_weather_test(args)
        return
    
    if not args.command:
        parser.print_help()
    else:
        commands[args.command](args)


if __name__ == "__main__":
    main()
