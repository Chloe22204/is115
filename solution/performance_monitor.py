"""Calculate performance metrics from one simulation run's event log."""

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from simulator.loaders import day_input_paths


def parse_time(time_str: str) -> float:
    """Convert an 'HH:MM' string to floating-point minutes after midnight."""
    if not time_str:
        return 0.0
    hours, minutes = map(int, time_str.split(":"))
    return float(hours * 60 + minutes)


def calculate_metrics(
    parcels: List[Dict[str, str]],
    distances: List[Dict[str, str]],
    config: Dict[str, Any],
    events: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Return performance metrics including trip capacity utilization and custom total penalty."""
    # 1. Map parcel sizes for trip capacity diagnostics
    parcel_sizes = {p["parcel_id"]: float(p["size"]) for p in parcels}
    capacity = float(config["capacity"])

    # 2. Track trips and collect delivery timestamps from event logs
    number_of_trips = 0
    trip_totals: Dict[Tuple[int, int], float] = {}
    delivery_times: Dict[str, float] = {}

    for event in events:
        event_type = event.get("event_type")
        if event_type == "hub_departure":
            number_of_trips += 1
        elif event_type == "delivery":
            key = (event["vehicle_id"], event["trip_id"])
            size = parcel_sizes[event["parcel_id"]]
            trip_totals[key] = trip_totals.get(key, 0.0) + size
            # Capture delivery time in minutes after midnight
            delivery_times[event["parcel_id"]] = float(event["time"])

    # 3. Format per-trip capacity diagnostics
    trips_summary = []
    for (vehicle_id, trip_id), total_size in sorted(trip_totals.items()):
        utilization_pct = (total_size / capacity * 100.0) if capacity > 0 else 0.0
        trips_summary.append({
            "vehicle_id": vehicle_id,
            "trip_id": trip_id,
            "total_size": round(total_size, 2),
            "capacity_utilisation_pct": round(utilization_pct, 2),
        })

    # 4. Calculate delivery window deviations and parcel metrics
    total_parcels = len(parcels)
    delivered_parcels = 0
    undelivered_parcels = 0
    total_early_minutes = 0.0
    total_late_minutes = 0.0

    for p in parcels:
        pid = p["parcel_id"]
        window_start = parse_time(p.get("delivery_window_start", "00:00"))
        window_end = parse_time(p["delivery_window_end"])

        if pid in delivery_times:
            delivered_parcels += 1
            deliv_time = delivery_times[pid]
            if deliv_time < window_start:
                total_early_minutes += (window_start - deliv_time)
            elif deliv_time > window_end:
                total_late_minutes += (deliv_time - window_end)
        else:
            undelivered_parcels += 1

    delivery_rate_pct = round((delivered_parcels / total_parcels * 100.0), 2) if total_parcels > 0 else 0.0
    total_penalty = (240.0 * undelivered_parcels) + total_early_minutes + total_late_minutes

    return {
        "number_of_trips": number_of_trips,
        "trips": trips_summary,
        "total_parcels": total_parcels,
        "delivered_parcels": delivered_parcels,
        "undelivered_parcels": undelivered_parcels,
        "delivery_rate_pct": delivery_rate_pct,
        "total_early_minutes": round(total_early_minutes, 2),
        "total_late_minutes": round(total_late_minutes, 2),
        "total_penalty": round(total_penalty, 2),
    }


def main(argv: Optional[List[str]] = None) -> int:
    """Load one day's inputs and event log, then write the metrics report."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"),
                        help="directory containing dist.csv, config.json and demand/")
    parser.add_argument("--day", required=True, help="day identifier, for example day_001")
    parser.add_argument("--log", type=Path, required=True,
                        help="event log from a simulator run")
    parser.add_argument("--output", type=Path,
                        help="JSON report (default: metrics.json beside the selected log)")
    args = parser.parse_args(argv)
    try:
        parcel_path, distance_path, config_path = day_input_paths(args.data, args.day)
        output = args.output if args.output is not None else args.log.with_name("metrics.json")
        # The input files all live in the data directory, so this also protects them.
        if output.resolve() == args.data.resolve() or args.data.resolve() in output.resolve().parents:
            raise ValueError("report output must be outside the input data directory")
        if output.resolve() == args.log.resolve():
            raise ValueError("report output must not overwrite the log")
        with parcel_path.open(newline="", encoding="utf-8-sig") as stream:
            parcels = list(csv.DictReader(stream))
        with distance_path.open(newline="", encoding="utf-8-sig") as stream:
            distances = list(csv.DictReader(stream))
        config = json.loads(config_path.read_text(encoding="utf-8-sig"))
        with args.log.open(encoding="utf-8") as stream:
            events = [json.loads(line) for line in stream if line.strip()]
        metrics = calculate_metrics(parcels, distances, config, events)
        report = json.dumps(metrics, indent=2, allow_nan=False) + "\n"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(f"Metrics report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
