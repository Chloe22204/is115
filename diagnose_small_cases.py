"""Compare deadline + 2-opt with exhaustive search on bounded real-data cases.

Run from the repository root. Saved simulations are not overwritten. Outputs:
results/small_case_diagnosis.json. This diagnoses a single-trip surrogate
objective; parcels left out are charged 240 even though another trip could
serve them in the full simulation. It is not a full-day optimality proof.
"""

import copy
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

from simulator.simulator import Simulator
from solution.policies.deadline_first import dispatch as build
from solution.policies.deadline_two_opt import dispatch as heuristic


def route_values(route, parcels, context):
    """Independently evaluate a bounded case, including its omitted parcels."""
    location = "HUB"
    departure = context["current_time"] + context["departure_delay"]
    time = departure
    load = early = late = 0.0
    legs = []
    for pid in route:
        record = parcels[pid]
        destination = record["delivery_location_id"]
        leg = context["travel_distance"][location][destination]
        legs.append(leg)
        time += leg
        load += record["size"]
        early += max(0.0, record["delivery_window_start"] - time)
        late += max(0.0, time - record["delivery_window_end"])
        location = destination
    distance = math.fsum(legs + [context["travel_distance"][location]["HUB"]])
    feasible = (
        load <= context["capacity"] + 1e-9
        and distance <= context["max_trip_distance_km"] + 1e-9
        and departure + distance <= context["return_cutoff"]
    )
    return {
        "route": list(route), "selected": len(route), "load": load,
        "distance": distance, "return_time": departure + distance,
        "early_minutes": early, "late_minutes": late, "feasible": feasible,
        "score": 240 * (len(parcels) - len(route)) + early + late,
    }


def exact_search(parcels, context):
    """Visit every ordered subset of at most eight parcels, including empty."""
    ids = sorted(parcels)
    if len(ids) > 8:
        raise ValueError("Exhaustive diagnostic is limited to eight parcels")
    best = None
    examined = 0
    feasible = 0

    def visit(route, remaining):
        nonlocal best, examined, feasible
        examined += 1
        value = route_values(route, parcels, context)
        if value["feasible"]:
            feasible += 1
            key = (value["score"], value["distance"], tuple(route))
            if best is None or key < (best["score"], best["distance"], tuple(best["route"])):
                best = value
        # No feasibility pruning: all ordered subsets are explicitly covered.
        for index, pid in enumerate(remaining):
            visit(route + [pid], remaining[:index] + remaining[index + 1:])

    visit([], ids)
    expected = sum(math.factorial(len(ids)) // math.factorial(len(ids) - k)
                   for k in range(len(ids) + 1))
    assert examined == expected
    return best, examined, feasible


def choose_pool(waiting, context):
    """Deterministically sample urgency and location diversity; not random."""
    selected = []
    locations = set()
    ordered = sorted(waiting, key=lambda pid: (waiting[pid]["delivery_window_end"], pid))
    nearby = sorted(waiting, key=lambda pid: (
        context["travel_distance"]["HUB"][waiting[pid]["delivery_location_id"]], pid))
    for ordering, limit in ((ordered, 4), (nearby, 8)):
        for pid in ordering:
            location = waiting[pid]["delivery_location_id"]
            if pid not in selected and location not in locations:
                selected.append(pid)
                locations.add(location)
            if len(selected) >= limit:
                break
    for pid in ordered:
        if len(selected) >= 8:
            break
        if pid not in selected:
            selected.append(pid)
    return {pid: copy.deepcopy(waiting[pid]) for pid in selected}


def collect_cases():
    cases = []
    targets = [("opening", 480), ("morning", 630), ("noon", 720), ("afternoon", 900)]
    with TemporaryDirectory(prefix="is115-small-cases-") as directory:
        for day_number in (1, 7, 16):
            day = f"day_{day_number:03d}"
            captured = set()

            def capture(parcels, context):
                waiting = {pid: p for pid, p in parcels.items()
                           if p["vehicle_assigned"] is None and p["delivery_time"] is None}
                for label, threshold in targets:
                    if label in captured or context["current_time"] < threshold or not waiting:
                        continue
                    captured.add(label)
                    pool = choose_pool(waiting, context)
                    source = dict(day=day, label=label, vehicle=context["vehicle_id"],
                                  planning_time=context["current_time"],
                                  source_waiting_count=len(waiting))
                    cases.append(dict(**source, kind="complete waiting set" if len(waiting) <= 8
                                      else "reduced waiting set", parcels=pool,
                                      context=copy.deepcopy(context), fixed_prefix=[]))
                    # Add one capacity-constrained suffix case per day's noon snapshot.
                    if label == "noon":
                        initial = build(parcels, context)
                        prefix = []
                        load = 0.0
                        for pid in initial:
                            if load >= 25.0:
                                break
                            prefix.append(pid)
                            load += parcels[pid]["size"]
                        if prefix and load >= 25.0 and len(prefix) < len(initial):
                            prefix_value = route_values(prefix, waiting, context)
                            location = parcels[prefix[-1]]["delivery_location_id"]
                            distances = context["travel_distance"]
                            prefix_distance = prefix_value["distance"] - distances[location]["HUB"]
                            suffix_context = copy.deepcopy(context)
                            suffix_context["current_time"] += prefix_distance
                            suffix_context["capacity"] -= load
                            suffix_context["max_trip_distance_km"] -= prefix_distance
                            # Virtual HUB starts at the prefix endpoint; returns still go to the real hub.
                            suffix_context["travel_distance"]["HUB"] = dict(distances[location])
                            suffix_context["travel_distance"]["HUB"]["HUB"] = distances[location]["HUB"]
                            remaining = {pid: p for pid, p in waiting.items() if pid not in prefix}
                            cases.append(dict(**source, kind="reduced set after fixed prefix",
                                              parcels=choose_pool(remaining, suffix_context),
                                              context=suffix_context, fixed_prefix=prefix))
                return heuristic(parcels, context)

            log = Path(directory) / "log.txt"
            sim = Simulator(f"data/demand/{day}.csv", "data/dist.csv", "data/config.json",
                            dispatch_policy=capture)
            sim.run(log)
            assert log.read_bytes() == Path(f"results/deadline_two_opt/{day}/log.txt").read_bytes()
    return cases


def main():
    cases = collect_cases()
    results = []
    for case in cases:
        parcels, context = case["parcels"], case["context"]
        route = heuristic(parcels, context)
        value = route_values(route, parcels, context)
        optimal, examined, feasible = exact_search(parcels, context)
        assert value["feasible"] and optimal is not None
        gap = value["score"] - optimal["score"]
        assert gap >= -1e-7
        # Separately find the best ordering of exactly the heuristic's selected set.
        import itertools
        same_set = min((route_values(order, parcels, context)
                        for order in itertools.permutations(route)),
                       key=lambda r: r["score"] if r["feasible"] else math.inf)
        result = {**case, "heuristic": value, "optimal": optimal,
                  "best_same_set": same_set, "gap": gap,
                  "ordered_subsets_examined": examined, "feasible_routes": feasible}
        results.append(result)
        print(json.dumps({"day": case["day"], "label": case["label"], "kind": case["kind"],
                          "candidates": len(parcels), "remaining_capacity": context["capacity"],
                          "heuristic_score": value["score"], "optimal_score": optimal["score"],
                          "gap": gap, "same_set_score": same_set["score"]}), flush=True)
    output = Path("results/small_case_diagnosis.json")
    output.write_text(json.dumps({"objective": "timing + 240 per parcel omitted from this single trip",
                                 "warning": "Exact only for each bounded subproblem; not a full-day objective or an untouched test set.",
                                 "cases": results}, indent=2, allow_nan=False) + "\n")
    print(f"Saved {len(results)} cases to {output}", flush=True)


if __name__ == "__main__":
    main()
