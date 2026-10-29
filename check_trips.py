"""Check every logged trip against the hard constraints, independently of the simulator.

Usage: python3 check_trips.py <policy> [<policy> ...]
Reads results/<policy>/day_XXX/log.txt, data/demand/day_XXX.csv, data/dist.csv and
data/config.json. Writes nothing. Exits with status 1 if any violation is found.
"""

import csv
import json
import math
import sys
from pathlib import Path

RESULTS = Path("results")
DATA = Path("data")
DAYS = [f"day_{i:03d}" for i in range(1, 21)]
RETURN_CUTOFF = 18 * 60.0  # 18:00 in minutes after midnight
TOLERANCE = 1e-9  # same float allowance the simulator uses


def fail(message):
    """Print a clear error and stop, rather than skipping anything silently."""
    print(f"Error: {message}")
    sys.exit(2)


def require(path):
    """Stop if an input file is missing."""
    if not path.is_file():
        fail(f"missing {path}")
    return path


def to_minutes(hhmm):
    """Convert 'HH:MM' to minutes after midnight."""
    hours, minutes = map(int, hhmm.split(":"))
    return float(hours * 60 + minutes)


def load_distances():
    """Return {origin: {destination: km}} from dist.csv (directed)."""
    distances = {}
    with require(DATA / "dist.csv").open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            distances.setdefault(row["location_1"], {})[row["location_2"]] = float(row["dist"])
    return distances


def load_demand(day):
    """Return {parcel_id: row} for one day's demand file."""
    path = require(DATA / "demand" / f"{day}.csv")
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return {row["parcel_id"]: row for row in csv.DictReader(stream)}


def check_day(policy, day, demand, distances, config):
    """Return (trips checked, list of violation messages) for one policy-day."""
    log = require(RESULTS / policy / day / "log.txt")
    departures = {}  # (vehicle, trip) -> departure time
    stops = {}  # (vehicle, trip) -> [(delivery time, parcel_id)] in log order
    delivery_count = {}
    with log.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            event = json.loads(line)
            kind = event.get("event_type")
            if kind == "hub_departure":
                departures[(event["vehicle_id"], event["trip_id"])] = float(event["time"])
            elif kind == "delivery":
                key = (event["vehicle_id"], event["trip_id"])
                stops.setdefault(key, []).append((float(event["time"]), event["parcel_id"]))
                delivery_count[event["parcel_id"]] = delivery_count.get(event["parcel_id"], 0) + 1

    violations = []

    def flag(where, message):
        violations.append(f"{policy} {day} {where}: {message}")

    # Parcel-level checks: delivered once, exists in demand, not delivered before arrival.
    for parcel_id, count in sorted(delivery_count.items()):
        if parcel_id not in demand:
            flag(f"parcel {parcel_id}", "delivered but not in demand file")
        if count != 1:
            flag(f"parcel {parcel_id}", f"delivered {count} times")
    for key, trip_stops in stops.items():
        for time, parcel_id in trip_stops:
            if parcel_id in demand and time < to_minutes(demand[parcel_id]["arrival_time"]):
                flag(f"vehicle {key[0]} trip {key[1]}",
                     f"parcel {parcel_id} delivered at {time:g} before arrival "
                     f"{demand[parcel_id]['arrival_time']}")

    # Deliveries must belong to a logged departure.
    for key in sorted(set(stops) - set(departures)):
        flag(f"vehicle {key[0]} trip {key[1]}", "deliveries without a hub_departure")

    # Trip-level checks for every logged departure.
    for key in sorted(departures):
        where = f"vehicle {key[0]} trip {key[1]}"
        trip_stops = stops.get(key, [])
        if not trip_stops:
            flag(where, "departure with no deliveries")
            continue
        # Visit stops in delivery-time order (stable sort keeps log order for ties).
        ordered = [pid for _, pid in sorted(trip_stops, key=lambda s: s[0])]
        known = [pid for pid in ordered if pid in demand]

        # Capacity: total size of parcels delivered on this trip.
        load = math.fsum(float(demand[pid]["size"]) for pid in known)
        if load > config["capacity"] + TOLERANCE:
            flag(where, f"load {load:g} > capacity {config['capacity']}")

        # Range: hub -> stops in delivery order -> hub.
        route = ["HUB"] + [demand[pid]["delivery_location_id"] for pid in known] + ["HUB"]
        try:
            distance = math.fsum(distances[a][b] for a, b in zip(route, route[1:]))
        except KeyError as exc:
            flag(where, f"no distance for location {exc}")
            continue
        if distance > config["vehicle_range_km"] + TOLERANCE:
            flag(where, f"round trip {distance:.3f} km > range {config['vehicle_range_km']}")

        # Return cutoff: departure + round trip (1 km = 1 minute) by 18:00.
        return_time = departures[key] + distance
        if return_time > RETURN_CUTOFF + TOLERANCE:
            flag(where, f"returns at {return_time:.3f} > {RETURN_CUTOFF:g} (18:00)")

    return len(departures), violations


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check_trips.py <policy> [<policy> ...]")
        sys.exit(2)
    policies = sys.argv[1:]
    for policy in policies:
        if not (RESULTS / policy).is_dir():
            fail(f"no results folder {RESULTS / policy}")

    config = json.loads(require(DATA / "config.json").read_text(encoding="utf-8-sig"))
    distances = load_distances()
    demand_by_day = {day: load_demand(day) for day in DAYS}

    all_violations = []
    print(f"{'policy':<24}{'trips checked':>14}{'violations':>12}")
    for policy in policies:
        trips = 0
        violations = []
        for day in DAYS:
            n, v = check_day(policy, day, demand_by_day[day], distances, config)
            trips += n
            violations += v
        print(f"{policy:<24}{trips:>14}{len(violations):>12}")
        all_violations += violations

    # List every violation, then exit non-zero if there were any.
    if all_violations:
        print("\nViolations:")
        for message in all_violations:
            print(f"  {message}")
        sys.exit(1)
    print("\nNo violations.")


if __name__ == "__main__":
    main()
