import itertools
import math
from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.deadline_two_opt import dispatch as initial_dispatch
from solution.policies.two_opt_helper import route_timing_penalty, two_opt


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Try bounded one-for-two exchanges after deadline-first + 2-opt.

    Inspect the four largest selected parcels and eight smallest waiting ones.
    Replace one selected stop by an adjacent pair in either order. Accept only
    strict improvements to timing minus 240 per carried parcel, then rerun 2-opt.
    """
    route = initial_dispatch(parcel, context)
    distances = context["travel_distance"]
    while route:
        selected = set(route)
        waiting = sorted(
            (pid for pid, record in parcel.items()
             if pid not in selected and record["vehicle_assigned"] is None
             and record["delivery_time"] is None),
            key=lambda pid: (
                parcel[pid]["size"], parcel[pid]["delivery_window_end"],
                distances["HUB"][parcel[pid]["delivery_location_id"]], pid,
            ),
        )[:8]
        if len(waiting) < 2:
            break
        removable = sorted(route, key=lambda pid: (
            -parcel[pid]["size"], -parcel[pid]["delivery_window_end"], pid,
        ))[:4]
        load = math.fsum(parcel[pid]["size"] for pid in route)
        current_penalty = route_timing_penalty(route, parcel, context)
        if current_penalty is None:
            raise ValueError("Starting route is infeasible")
        best_key = None
        best_route = None

        for removed in removable:
            position = route.index(removed)
            for first, second in itertools.combinations(waiting, 2):
                candidate_load = load - parcel[removed]["size"] + parcel[first]["size"] + parcel[second]["size"]
                if candidate_load > context["capacity"] + 1e-9:
                    continue
                for pair in ((first, second), (second, first)):
                    candidate = route[:position] + list(pair) + route[position + 1:]
                    penalty = route_timing_penalty(candidate, parcel, context)
                    if penalty is None:
                        continue
                    change = penalty - current_penalty - 240.0
                    if change >= -1e-9:
                        continue
                    locations = ["HUB"] + [
                        parcel[pid]["delivery_location_id"] for pid in candidate
                    ] + ["HUB"]
                    distance = math.fsum(
                        distances[a][b] for a, b in zip(locations, locations[1:])
                    )
                    key = (change, distance, removed, pair[0], pair[1])
                    if best_key is None or key < best_key:
                        best_key = key
                        best_route = candidate

        if best_route is None:
            break
        # Every accepted exchange increases the selected count by one, preventing cycles.
        route = two_opt(best_route, parcel, context)

    return route
