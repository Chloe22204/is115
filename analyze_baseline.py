import csv
import json
import sys
from pathlib import Path


def parse_time(time_str: str) -> float:
    """Convert an HH:MM time string to floating-point minutes after midnight."""
    hour, minute = map(int, time_str.strip().split(":"))
    return float(hour * 60 + minute)


def load_distances(dist_path: Path) -> dict:
    """Load distances from dist.csv into a nested dict: distances[origin][destination] = dist_km."""
    distances = {}
    with dist_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            origin = row["location_1"].strip()
            dest = row["location_2"].strip()
            dist = float(row["dist"])
            distances.setdefault(origin, {})[dest] = dist
    return distances


def load_demand(demand_path: Path) -> dict:
    """Load demand file into a dict mapping parcel_id to its properties."""
    parcels = {}
    with demand_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row["parcel_id"].strip()
            parcels[pid] = {
                "size": float(row["size"]),
                "delivery_location_id": row["delivery_location_id"].strip(),
                "delivery_window_end": parse_time(row["delivery_window_end"]),
            }
    return parcels


def analyze_day(day_str: str, results_folder: str, distances: dict):
    """Analyze a single day and return calculated metrics."""
    demand_file = Path("data") / "demand" / f"{day_str}.csv"
    log_file = Path("results") / results_folder / day_str / "log.txt"

    # Step 1: Check if input files exist
    if not demand_file.exists():
        print(f"Error: Missing demand file: {demand_file}")
        sys.exit(1)
    if not log_file.exists():
        print(f"Error: Missing log file: {log_file}")
        sys.exit(1)

    # Step 2: Load demand data for parcel size, location, and deadlines
    parcels = load_demand(demand_file)
    total_parcels = len(parcels)

    # Step 3: Parse event log
    deliveries = []
    hub_departures = []

    with log_file.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            event = json.loads(line)
            event_type = event.get("event_type")
            if event_type == "delivery":
                deliveries.append(event)
            elif event_type == "hub_departure":
                hub_departures.append(event)

    # Metric 1: Total & Delivered parcels
    num_delivered = len(deliveries)

    # Metric 2: Number of trips (distinct vehicle_id & trip_id)
    trips_keys = set((e["vehicle_id"], e["trip_id"]) for e in hub_departures)
    num_trips = len(trips_keys)

    # Metric 6: Time of last hub departure
    last_departure_time = max((e["time"] for e in hub_departures), default=0.0)

    # Metric 5: Late deliveries
    late_deliveries = 0
    for d in deliveries:
        pid = d["parcel_id"]
        delivery_time = d["time"]
        deadline = parcels[pid]["delivery_window_end"]
        if delivery_time > deadline:
            late_deliveries += 1

    # Metrics 3 & 4: Load and Round-trip distance per trip
    # Group deliveries by (vehicle_id, trip_id) sorted chronologically
    trip_deliveries = {}
    for d in deliveries:
        key = (d["vehicle_id"], d["trip_id"])
        trip_deliveries.setdefault(key, []).append(d)

    for key in trip_deliveries:
        trip_deliveries[key].sort(key=lambda x: x["time"])

    trip_loads = []
    trip_distances = []

    for key in trips_keys:
        d_list = trip_deliveries.get(key, [])

        # Calculate trip load
        load = sum(parcels[d["parcel_id"]]["size"] for d in d_list)
        trip_loads.append(load)

        # Calculate round-trip distance along route: HUB -> loc1 -> loc2 -> ... -> HUB
        dist = 0.0
        current_loc = "HUB"
        for d in d_list:
            next_loc = parcels[d["parcel_id"]]["delivery_location_id"]
            dist += distances[current_loc][next_loc]
            current_loc = next_loc
        dist += distances[current_loc]["HUB"]
        trip_distances.append(dist)

    avg_load = (sum(trip_loads) / num_trips) if num_trips > 0 else 0.0
    max_load = max(trip_loads, default=0.0)
    avg_dist = (sum(trip_distances) / num_trips) if num_trips > 0 else 0.0

    return {
        "day": day_str,
        "total_parcels": total_parcels,
        "delivered_parcels": num_delivered,
        "trips": num_trips,
        "avg_load": avg_load,
        "max_load": max_load,
        "avg_dist": avg_dist,
        "late_deliveries": late_deliveries,
        "last_departure": last_departure_time,
        "trip_loads": trip_loads,
        "trip_distances": trip_distances,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_baseline.py <results_folder_name>")
        sys.exit(1)

    results_folder = sys.argv[1]
    dist_file = Path("data") / "dist.csv"

    if not dist_file.exists():
        print(f"Error: Missing distance file: {dist_file}")
        sys.exit(1)

    distances = load_distances(dist_file)

    results = []
    all_trip_loads = []
    all_trip_distances = []

    # Analyze days 001 to 020
    for i in range(1, 21):
        day_str = f"day_{i:03d}"
        res = analyze_day(day_str, results_folder, distances)
        results.append(res)
        all_trip_loads.extend(res["trip_loads"])
        all_trip_distances.extend(res["trip_distances"])

    # Print Table Header
    header = (
        f"{'Day':<10} | {'Parcels (Del/Tot)':<18} | {'Trips':<6} | "
        f"{'Avg Load':<9} | {'Max Load':<9} | {'Avg Dist (km)':<13} | "
        f"{'Late Parcels (%)':<18} | {'Last Dep':<8}"
    )
    print(header)
    print("-" * len(header))

    # Print per-day rows
    tot_parcels = sum(r["total_parcels"] for r in results)
    tot_delivered = sum(r["delivered_parcels"] for r in results)
    tot_trips = sum(r["trips"] for r in results)
    tot_late = sum(r["late_deliveries"] for r in results)
    max_load_overall = max((r["max_load"] for r in results), default=0.0)
    last_dep_overall = max((r["last_departure"] for r in results), default=0.0)

    for r in results:
        deliv_str = f"{r['delivered_parcels']}/{r['total_parcels']}"
        late_pct = (r["late_deliveries"] / r["delivered_parcels"] * 100) if r["delivered_parcels"] > 0 else 0.0
        late_str = f"{r['late_deliveries']} ({late_pct:.1f}%)"
        last_dep_hhmm = f"{int(r['last_departure'] // 60):02d}:{int(r['last_departure'] % 60):02d}"

        print(
            f"{r['day']:<10} | {deliv_str:<18} | {r['trips']:<6} | "
            f"{r['avg_load']:<9.2f} | {r['max_load']:<9.2f} | {r['avg_dist']:<13.2f} | "
            f"{late_str:<18} | {last_dep_hhmm:<8}"
        )

    print("-" * len(header))

    # Calculate and print Summary Totals Row
    overall_avg_load = (sum(all_trip_loads) / tot_trips) if tot_trips > 0 else 0.0
    overall_avg_dist = (sum(all_trip_distances) / tot_trips) if tot_trips > 0 else 0.0
    overall_late_pct = (tot_late / tot_delivered * 100) if tot_delivered > 0 else 0.0
    overall_late_str = f"{tot_late} ({overall_late_pct:.1f}%)"
    overall_last_dep_hhmm = f"{int(last_dep_overall // 60):02d}:{int(last_dep_overall % 60):02d}"
    tot_deliv_str = f"{tot_delivered}/{tot_parcels}"

    print(
        f"{'TOTAL':<10} | {tot_deliv_str:<18} | {tot_trips:<6} | "
        f"{overall_avg_load:<9.2f} | {max_load_overall:<9.2f} | {overall_avg_dist:<13.2f} | "
        f"{overall_late_str:<18} | {overall_last_dep_hhmm:<8}"
    )

    # Print summary distribution metrics across all trips
    print("\n--- Additional Trip Insights ---")
    if tot_trips > 0:
        share_load_27 = (sum(1 for l in all_trip_loads if l >= 27) / tot_trips) * 100
        share_dist_300 = (sum(1 for d in all_trip_distances if d >= 300) / tot_trips) * 100
        print(f"Share of trips with load >= 27: {share_load_27:.2f}%")
        print(f"Share of trips with round-trip distance >= 300 km: {share_dist_300:.2f}%")
    else:
        print("No trips recorded.")


if __name__ == "__main__":
    main()