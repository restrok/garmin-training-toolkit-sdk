#!/usr/bin/env python3
"""
Garmin Training System CLI
Unified command interface using local data files.
"""

import argparse
import json
import logging
import subprocess
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
        client = get_authenticated_client(token_file)
        client.get_user_profile()
    except Exception as e:
        if "401" in str(e) or "Unauthorized" in str(e) or "not set" in str(e).lower():
            print("Session expired. Re-authenticating...")
            subprocess.run(["python3", str(Path(__file__).parent / "garmin.py"), "auth"], check=True)
            token_file = find_token_file()
            client = get_authenticated_client(token_file)
    
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
    
    print(f"\n📊 Running")
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
    data = load_report()
    if not data:
        return
    
    activities = data.get("activities", [])
    running = [a for a in activities if a.get("type") == "running"]
    
    hr_values = [a.get("avg_hr", 0) for a in running if a.get("avg_hr")]
    
    if not hr_values or len(hr_values) < 5:
        print("Need at least 5 runs to calculate zones.")
        return
    
    hrs_sorted = sorted(hr_values)
    n = len(hrs_sorted)
    
    p25 = hrs_sorted[n // 4]
    p75 = hrs_sorted[3 * n // 4]
    max_hr = max(a.get("max_hr", 0) for a in running if a.get("max_hr")) or max(hr_values) + 20
    
    print(f"\n{'='*50}")
    print("DATA-DRIVEN HR ZONES")
    print(f"{'='*50}")
    print(f"Based on {len(running)} runs")
    print(f"")
    print(f"  Z1 (Recovery): <{int(p25-5)} bpm")
    print(f"  Z2 (Easy):      {int(p25-5)}-{int(p25+5)} bpm  (conversational)")
    print(f"  Z3 (Tempo):     {int(p25+6)}-{int(p75)} bpm")
    print(f"  Z4 (Threshold): {int(p75+1)}-{int(max_hr-20)} bpm")
    print(f"  Z5 (Max):       >{int(max_hr-20)} bpm")
    print(f"")
    print(f"Distribution:")
    for name, low, high in [('Z2', p25-5, p25+6), ('Z3', p25+6, p75+1), ('Z4+', p75+1, 200)]:
        count = sum(1 for a in running if low <= a.get('avg_hr', 0) < high)
        pct = count / len(running) * 100
        bar = '█' * int(pct/5) if pct > 5 else ''
        print(f"  {name}: {pct:.0f}% {bar}")
    print(f"")
    print(f"💡 Update Garmin Connect HR zones to match these values!")
    print(f"{'='*50}")


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
        print(f"\n💓 No HRV data")
    
    readiness = data.get("training_readiness", [])
    if readiness:
        vals = [r.get("value", 0) for r in readiness if r.get("value")]
        if vals:
            print(f"\n📈 Readiness: {sum(vals)/len(vals):.0f}/100")
    else:
        print(f"\n📈 No readiness data")
    
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
        print(f"Garmin:")
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
            
            print(f"\n📈 Realistic (Riegel formula, median best 3):")
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
        
        print(f"\n⚠️  Training Issue:")
        print(f"  Avg HR: {avg_hr:.0f} bpm ({avg_hr/max_hr*100:.0f}% max)")
        print(f"  Zone 4: {zone4_pct:.0f}% (target: ~20%)")
    
    print(f"\n{'='*60}")


def cmd_plan(args):
    """Generate new plan."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent / "garmin-analyzer"))
    from plan_generator import main as gen_main
    gen_main()


def cmd_auth(args):
    """Run browser authentication."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from garmin_auth import main as auth_main
    auth_main()


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
        client = get_authenticated_client(token_file)
    except Exception as e:
        if "401" in str(e) or "Unauthorized" in str(e):
            print("Session expired. Re-authenticating...")
            subprocess.run(["python3", str(Path(__file__).parent / "garmin.py"), "auth"], check=True)
            client = get_authenticated_client(find_token_file())
        else:
            raise
    
    # Pass args to uploader
    sys.argv = ["garmin_workout_uploader.py"]
    if args.clean:
        if args.clean == "all":
            sys.argv.append("--clean-all")
        else:
            sys.argv.extend(["--clean", args.clean])
    sys.argv.append("--yes")
    
    sys.path.insert(0, str(Path(__file__).parent / "garmin-workout-uploader"))
    from garmin_workout_uploader import main as upload_main
    upload_main()


def main():
    parser = argparse.ArgumentParser(description="Garmin Training System")
    sub = parser.add_subparsers(dest="command")
    
    sub.add_parser("collect", help="Collect data from Garmin")
    
    p_progress = sub.add_parser("progress", help="Show progress")
    p_progress.add_argument("--days", type=int, default=90)
    
    sub.add_parser("zones", help="Show personalized HR zones")
    sub.add_parser("recovery", help="Show recovery status")
    sub.add_parser("predict", help="Race predictions")
    
    p_best = sub.add_parser("best", help="Best race times")
    p_best.add_argument("--distance", default="10k")
    p_best.add_argument("--limit", type=int, default=5)
    
    sub.add_parser("compare", help="Compare plans")
    
    p_export = sub.add_parser("export", help="Export full report")
    p_export.add_argument("--file", help="Save to file")
    
    p_upload = sub.add_parser("upload", help="Upload workouts")
    p_upload.add_argument("--clean", nargs="?", const="all", help="Delete old workouts (use --clean-all or month prefix)")
    p_upload.add_argument("--delete", metavar="WORKOUT_ID", help="Delete specific workout by ID")
    
    sub.add_parser("plan", help="Generate training plan")
    
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
    }
    
    if not args.command:
        parser.print_help()
    else:
        commands[args.command](args)


if __name__ == "__main__":
    main()
