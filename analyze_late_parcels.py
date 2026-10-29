"""Measure how often delivered parcels are very late, per policy, from existing logs only.

Reads results/<policy>/day_XXX/log.txt and data/demand/day_XXX.csv. Writes nothing.
"""

import csv
import json
import sys
from pathlib import Path

RESULTS = Path("results")
DEMAND = Path("data") / "demand"
DAYS = [f"day_{i:03d}" for i in range(1, 21)]
THRESHOLDS = [60, 120, 240]  # minutes late
UNDELIVERED_PENALTY = 240.0


def fail(message):
    """Print a clear error and stop, rather than skipping anything silently."""
    print(f"Error: {message}")
    sys.exit(1)


def to_minutes(hhmm):
    """Convert 'HH:MM' to minutes after midnight (empty counts as 0, as in the monitor)."""
    if not hhmm:
        return 0.0
    hours, minutes = map(int, hhmm.split(":"))
    return float(hours * 60 + minutes)


def load_windows(day):
    """Return {parcel_id: (window_start, window_end)} for one day's demand file."""
    path = DEMAND / f"{day}.csv"
    if not path.is_file():
        fail(f"missing {path}")
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return {row["parcel_id"]: (to_minutes(row.get("delivery_window_start", "")),
                                   to_minutes(row["delivery_window_end"]))
                for row in csv.DictReader(stream)}


def load_deliveries(path):
    """Return {parcel_id: delivery_time} from a log's delivery events."""
    if not path.is_file():
        fail(f"missing {path}")
    deliveries = {}
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                event = json.loads(line)
                if event.get("event_type") == "delivery":
                    deliveries[event["parcel_id"]] = float(event["time"])
    return deliveries


def analyse_policy(policy, windows_by_day):
    """Sum lateness statistics for one policy over all 20 days."""
    s = {"delivered": 0, "late": 0, "undelivered": 0, "late_min": 0.0,
         "late_min_240": 0.0, "early_min": 0.0, "max_late": 0.0}
    for t in THRESHOLDS:
        s[f"over_{t}"] = 0

    for day in DAYS:
        windows = windows_by_day[day]
        deliveries = load_deliveries(RESULTS / policy / day / "log.txt")
        for pid, (start, end) in windows.items():
            if pid not in deliveries:
                s["undelivered"] += 1
                continue
            s["delivered"] += 1
            time = deliveries[pid]
            # Same early/late rule as solution/performance_monitor.py
            if time < start:
                s["early_min"] += start - time
            elif time > end:
                late = time - end
                s["late"] += 1
                s["late_min"] += late
                s["max_late"] = max(s["max_late"], late)
                for t in THRESHOLDS:
                    if late > t:
                        s[f"over_{t}"] += 1
                if late > 240:
                    s["late_min_240"] += late
    return s


def main():
    # Policies are folders under results/ that contain day_XXX subfolders
    policies = sorted(p.name for p in RESULTS.iterdir()
                      if p.is_dir() and any(p.glob("day_*")))
    if not policies:
        fail(f"no policy folders found in {RESULTS}/")

    # Demand files are shared by all policies, so load each day once
    windows_by_day = {day: load_windows(day) for day in DAYS}
    stats = {policy: analyse_policy(policy, windows_by_day) for policy in policies}

    # Table 1: lateness counts per policy, summed over 20 days
    print(f"\n{'policy':<22}{'delivered':>10}{'late':>8}{'>60':>8}{'>120':>8}{'>240':>8}"
          f"{'late min':>12}{'min >240':>12}{'undeliv':>9}{'max late':>10}")
    for policy in policies:
        s = stats[policy]
        print(f"{policy:<22}{s['delivered']:>10}{s['late']:>8}{s['over_60']:>8}"
              f"{s['over_120']:>8}{s['over_240']:>8}{s['late_min']:>12.1f}"
              f"{s['late_min_240']:>12.1f}{s['undelivered']:>9}{s['max_late']:>10.1f}")

    # Table 2: share of the main metric from late minutes of parcels > 240 min late
    print(f"\n{'policy':<22}{'total penalty':>15}{'min >240':>12}{'share':>9}")
    for policy in policies:
        s = stats[policy]
        penalty = UNDELIVERED_PENALTY * s["undelivered"] + s["early_min"] + s["late_min"]
        share = s["late_min_240"] / penalty * 100 if penalty else 0.0
        print(f"{policy:<22}{penalty:>15.2f}{s['late_min_240']:>12.1f}{share:>8.1f}%")


if __name__ == "__main__":
    main()
