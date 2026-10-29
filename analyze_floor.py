"""Estimate the unavoidable-undelivered floor and fleet usage for two policies.

Reads data/demand/*.csv, data/dist.csv, data/config.json and
results/<policy>/day_XXX/log.txt for nearby_two_opt and deadline_two_opt. Writes nothing.
"""

import csv
import json
import math
import sys
from pathlib import Path

DATA = Path("data")
RESULTS = Path("results")
POLICIES = ["nearby_two_opt", "deadline_two_opt"]
DAYS = [f"day_{i:03d}" for i in range(1, 21)]
DAY_START = 8 * 60.0  # first planning tick, 08:00
TICK = 10.0  # planning interval in minutes
DEPARTURE_DELAY = 30.0
RETURN_CUTOFF = 18 * 60.0  # 1080
LAST_TICK = RETURN_CUTOFF - DEPARTURE_DELAY  # 17:30, the simulator's last planning tick
UNDELIVERED_PENALTY = 240
WINDOWS = [("08-09", 480, 540), ("09-12", 540, 720), ("12-15", 720, 900), ("15-18", 900, 1080)]


def fail(message):
    """Print a clear error and stop, rather than skipping anything silently."""
    print(f"Error: {message}")
    sys.exit(1)


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
    """Return {origin: {destination: km}} from dist.csv."""
    distances = {}
    with require(DATA / "dist.csv").open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            distances.setdefault(row["location_1"], {})[row["location_2"]] = float(row["dist"])
    return distances


def load_demand(day):
    """Return {parcel_id: row} for one day."""
    with require(DATA / "demand" / f"{day}.csv").open(newline="", encoding="utf-8-sig") as stream:
        return {row["parcel_id"]: row for row in csv.DictReader(stream)}


def undeliverable(demand, distances, vehicle_range):
    """Parcels that no policy can deliver, even alone at the first tick after arrival."""
    out = set()
    for pid, row in demand.items():
        arrival = to_minutes(row["arrival_time"])
        # First planning tick at or after arrival (arrivals are processed before planning)
        tick = DAY_START + max(0.0, math.ceil((arrival - DAY_START) / TICK)) * TICK
        location = row["delivery_location_id"]
        round_trip = distances["HUB"][location] + distances[location]["HUB"]
        if (tick > LAST_TICK
                or tick + DEPARTURE_DELAY + round_trip > RETURN_CUTOFF
                or round_trip > vehicle_range):
            out.add(pid)
    return out


def read_trips(policy, day, demand, distances):
    """Return (delivered parcel ids, list of (departure, return, load)) from one log."""
    departures, stops = {}, {}
    with require(RESULTS / policy / day / "log.txt").open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            event = json.loads(line)
            key = (event.get("vehicle_id"), event.get("trip_id"))
            if event["event_type"] == "hub_departure":
                departures[key] = float(event["time"])
            elif event["event_type"] == "delivery":
                stops.setdefault(key, []).append((float(event["time"]), event["parcel_id"]))
    delivered = set()
    trips = []
    for key, departure in departures.items():
        visits = sorted(stops.get(key, []))
        delivered.update(pid for _, pid in visits)
        load = math.fsum(float(demand[pid]["size"]) for _, pid in visits)
        # Return = last delivery time + drive from last stop back to the hub
        if visits:
            last = demand[visits[-1][1]]["delivery_location_id"]
            ret = visits[-1][0] + distances[last]["HUB"]
        else:
            ret = departure
        trips.append((departure, ret, load))
    return delivered, trips


def main():
    config = json.loads(require(DATA / "config.json").read_text(encoding="utf-8-sig"))
    distances = load_distances()
    vehicles = config["number_of_vehicles"]

    stats = {p: {"in_floor": 0, "undelivered": 0, "busy": 0.0, "trips": 0,
                 "win_load": [0.0] * len(WINDOWS), "win_trips": [0] * len(WINDOWS)}
             for p in POLICIES}
    per_day = []
    total_floor = 0
    for day in DAYS:
        demand = load_demand(day)
        floor = undeliverable(demand, distances, config["vehicle_range_km"])
        total_floor += len(floor)
        row = [day, len(demand), len(floor)]
        for p in POLICIES:
            delivered, trips = read_trips(p, day, demand, distances)
            undelivered = set(demand) - delivered
            s = stats[p]
            s["undelivered"] += len(undelivered)
            s["in_floor"] += len(undelivered & floor)
            # Busy time per trip = time away from the hub plus the 30-minute pre-departure delay
            s["busy"] += sum(ret - dep + DEPARTURE_DELAY for dep, ret, _ in trips)
            s["trips"] += len(trips)
            for dep, _, load in trips:
                for i, (_, lo, hi) in enumerate(WINDOWS):
                    if lo <= dep < hi or (hi == RETURN_CUTOFF and dep == hi):
                        s["win_load"][i] += load
                        s["win_trips"][i] += 1
            row += [len(undelivered), len(undelivered & floor)]
        per_day.append(row)

    # Per-day table: parcels, undeliverable floor, and each policy's undelivered (in floor)
    print(f"{'day':<9}{'parcels':>8}{'floor':>7}   {'nearby_two_opt undel (in floor)':>32}"
          f"   {'deadline_two_opt undel (in floor)':>34}")
    for day, n, f, nu, nf, du, df in per_day:
        print(f"{day:<9}{n:>8}{f:>7}   {f'{nu} ({nf})':>32}   {f'{du} ({df})':>34}")
    print(f"{'total':<9}{sum(r[1] for r in per_day):>8}{total_floor:>7}   "
          f"{f'{sum(r[3] for r in per_day)} ({sum(r[4] for r in per_day)})':>32}   "
          f"{f'{sum(r[5] for r in per_day)} ({sum(r[6] for r in per_day)})':>34}")

    # Policy summary over all 20 days
    available = vehicles * (RETURN_CUTOFF - DAY_START) * len(DAYS)  # vehicles x 600 min x days
    print(f"\n{'policy':<18}{'undelivered':>12}{'in floor':>10}{'floor penalty':>15}"
          f"{'busy share':>12}{'trips/day':>11}" + "".join(f"{'load ' + w:>12}" for w, _, _ in WINDOWS))
    for p in POLICIES:
        s = stats[p]
        loads = [s["win_load"][i] / s["win_trips"][i] if s["win_trips"][i] else 0.0
                 for i in range(len(WINDOWS))]
        print(f"{p:<18}{s['undelivered']:>12}{s['in_floor']:>10}"
              f"{UNDELIVERED_PENALTY * s['in_floor']:>15,}{s['busy'] / available * 100:>11.1f}%"
              f"{s['trips'] / len(DAYS):>11.2f}" + "".join(f"{x:>12.2f}" for x in loads))
    print(f"\nTrips per departure window: " + "; ".join(
        f"{p} " + ", ".join(f"{w}={stats[p]['win_trips'][i]}" for i, (w, _, _) in enumerate(WINDOWS))
        for p in POLICIES))
    print(f"Capacity {config['capacity']}, {vehicles} vehicles, range {config['vehicle_range_km']} km.")


if __name__ == "__main__":
    main()
