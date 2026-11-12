"""Compare the three predeclared geography settings without replacing saved results."""
import copy
import csv
import hashlib
import importlib
import json
import math
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import check_trips
from simulator.loaders import day_input_paths
from simulator.simulator import Simulator
from solution.performance_monitor import calculate_metrics

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / "plan.json").read_text())
CONTROL = PLAN["reference_policy"]
CANDIDATES = [f"geo_anchor{band}" for band in PLAN["bands_minutes"]]
NAMES = [CONTROL] + CANDIDATES


def rows(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def minutes(value):
    hours, mins = map(int, value.split(":"))
    return 60 * hours + mins


def run_day(name, number):
    day = f"day_{number:03d}"
    inputs = day_input_paths(ROOT / "data", day)
    demand_rows = rows(inputs[0])
    demand = {r["parcel_id"]: r for r in demand_rows}
    config = json.loads(inputs[2].read_text())
    policy = importlib.import_module("solution.policies." + name).dispatch
    calls = 0
    seconds = 0.0
    trips = []

    def checked(parcels, context):
        nonlocal calls, seconds
        calls += 1
        before_parcels = copy.deepcopy(parcels)
        before_context = copy.deepcopy(context)
        start = perf_counter()
        route = policy(parcels, context)
        seconds += perf_counter() - start
        assert parcels == before_parcels and context == before_context, "Input mutation"
        assert len(route) == len(set(route)), "Repeated parcel"
        for pid in route:
            assert pid in parcels
            p = parcels[pid]
            assert p["arrival_time"] <= context["current_time"]
            assert p["vehicle_assigned"] is None and p["delivery_time"] is None
        if route:
            load = math.fsum(parcels[pid]["size"] for pid in route)
            locations = ["HUB"] + [parcels[pid]["delivery_location_id"] for pid in route] + ["HUB"]
            distance = math.fsum(context["travel_distance"][a][b]
                                 for a, b in zip(locations, locations[1:]))
            departure = context["current_time"] + context["departure_delay"]
            assert load <= context["capacity"] + 1e-9
            assert distance <= context["max_trip_distance_km"] + 1e-9
            assert distance <= 125.0 + 1e-9
            assert departure + distance <= context["return_cutoff"] + 1e-9
            trips.append({"distance": distance, "capacity_pct": 100 * load / context["capacity"],
                          "destinations": len(set(locations) - {"HUB"})})
        return route

    folder = HERE / "results" / name / day
    folder.mkdir(parents=True, exist_ok=True)
    simulator = Simulator(*inputs, dispatch_policy=checked)
    simulator.run(folder / "log.txt")
    events = [json.loads(line) for line in (folder / "log.txt").read_text().splitlines()]
    metrics = calculate_metrics(demand_rows, rows(inputs[1]), config, events)
    (folder / "metrics.json").write_text(json.dumps(metrics, indent=2, allow_nan=False) + "\n")
    check_trips.RESULTS = HERE / "results"
    count, violations = check_trips.check_day(name, day, demand, simulator.distance, config)
    assert not violations, violations
    assert count == len(trips) == metrics["number_of_trips"]
    if name == CONTROL:
        for filename in ["log.txt", "metrics.json"]:
            assert (folder / filename).read_bytes() == (ROOT / "results" / CONTROL / day / filename).read_bytes()
    morning_late = math.fsum(
        max(0.0, event["time"] - minutes(demand[event["parcel_id"]]["delivery_window_end"]))
        for event in events if event["event_type"] == "delivery"
        and 480 <= minutes(demand[event["parcel_id"]]["arrival_time"]) < 600
    )
    return dict(day=day, **{k: v for k, v in metrics.items() if k != "trips"},
                morning_late_minutes=morning_late, driving_km=math.fsum(t["distance"] for t in trips),
                capacity_pct_sum=math.fsum(t["capacity_pct"] for t in trips),
                destinations_sum=sum(t["destinations"] for t in trips),
                max_trip_minutes=max((t["distance"] for t in trips), default=0),
                dispatch_calls=calls, dispatch_seconds=seconds)


def totals(daily):
    keys = ["total_penalty", "delivered_parcels", "undelivered_parcels", "total_early_minutes",
            "total_late_minutes", "number_of_trips", "morning_late_minutes", "driving_km",
            "dispatch_calls", "dispatch_seconds"]
    result = {k: math.fsum(r[k] for r in daily) for k in keys}
    result["mean_capacity_pct"] = math.fsum(r["capacity_pct_sum"] for r in daily) / result["number_of_trips"]
    result["mean_destinations_per_trip"] = math.fsum(r["destinations_sum"] for r in daily) / result["number_of_trips"]
    result["max_trip_minutes"] = max(r["max_trip_minutes"] for r in daily)
    return result


def main():
    protected_paths = [p for folder in ["data", "simulator", "solution"]
                       for p in (ROOT / folder).rglob("*") if p.is_file() and p.suffix in [".py", ".csv", ".json"]]
    protected = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected_paths}
    daily = {name: [] for name in NAMES}
    chosen = None
    for phase in [range(1, 11), range(11, 21)]:
        for number in phase:
            # Rotate order to reduce a fixed position effect on descriptive timings.
            offset = number % len(NAMES)
            for name in NAMES[offset:] + NAMES[:offset]:
                daily[name].append(run_day(name, number))
            print(f"Finished day {number:02d}: " + ", ".join(
                f"{name}={daily[name][-1]['total_penalty']:.2f}" for name in NAMES), flush=True)
        if chosen is None:
            chosen = min(CANDIDATES, key=lambda name: (totals(daily[name])["total_penalty"], CANDIDATES.index(name)))
            selection = {"chosen_from_days_1_to_10": chosen,
                         "first10_penalties": {name: totals(daily[name])["total_penalty"] for name in NAMES}}
            (HERE / "selection.json").write_text(json.dumps(selection, indent=2) + "\n")
            print("Selected before days 11-20:", chosen, flush=True)
    summary = {"plan": PLAN, "chosen_candidate": chosen, "policies": {}, "runs": 80,
               "violations": 0, "control_matches_saved_logs_and_metrics": 20,
               "timing_note": "One descriptive run; dispatch timing excludes snapshot checks and simulator work. Not a repeated benchmark.",
               "sources_sha256": protected}
    for name in NAMES:
        records = sorted(daily[name], key=lambda r: r["day"])
        values = totals(records)
        values["first10"] = totals(records[:10])["total_penalty"]
        values["last10"] = totals(records[10:])["total_penalty"]
        values["days_better_than_control"] = sum(r["total_penalty"] < c["total_penalty"] - 1e-9
                                                for r, c in zip(records, daily[CONTROL]))
        summary["policies"][name] = {"totals": values, "daily": records}
    reference = summary["policies"][CONTROL]["totals"]
    candidate = summary["policies"][chosen]["totals"]
    gain = 100 * (reference["last10"] - candidate["last10"]) / reference["last10"]
    summary["adoption_gate"] = {"development_no_worse": candidate["first10"] <= reference["first10"],
                                "comparison_improvement_pct": gain,
                                "passes": candidate["first10"] <= reference["first10"] and gain >= 2.0}
    summary["trips_checked"] = int(sum(p["totals"]["number_of_trips"] for p in summary["policies"].values()))
    for relative, expected in protected.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, relative
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"chosen": chosen, "adoption_gate": summary["adoption_gate"],
                      "totals": {n: p["totals"] for n, p in summary["policies"].items()}}, indent=2), flush=True)


if __name__ == "__main__":
    main()
