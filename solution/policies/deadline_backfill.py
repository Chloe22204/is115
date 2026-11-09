import math
from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.helpers import (
    build_deadline_two_opt as initial_dispatch,
    route_timing_penalty,
    two_opt,
)


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Insert beneficial waiting parcels into a deadline + 2-opt route.

    Each insertion must reduce timing penalty minus 240 per selected parcel.
    Existing selections are preserved. Reapply 2-opt after each insertion.
    This trip-level score is a proxy, not the full day's eventual penalty.
    """
    route = initial_dispatch(parcel, context)
    if not route:
        return route

    selected = set(route)
    waiting = sorted(
        pid for pid, record in parcel.items()
        if pid not in selected
        and record["vehicle_assigned"] is None
        and record["delivery_time"] is None
    )
    distances = context["travel_distance"]

    while waiting:
        load = math.fsum(parcel[pid]["size"] for pid in route)
        current_penalty = route_timing_penalty(route, parcel, context)
        if current_penalty is None:
            raise ValueError("Starting route is infeasible")
        best_key = None
        best_route = None
        best_pid = None

        for pid in waiting:
            record = parcel[pid]
            if load + record["size"] > context["capacity"] + 1e-9:
                continue
            for position in range(len(route) + 1):
                candidate = route[:position] + [pid] + route[position:]
                penalty = route_timing_penalty(candidate, parcel, context)
                if penalty is None:
                    continue
                change = penalty - current_penalty - 240.0
                if change >= -1e-9:
                    continue
                locations = ["HUB"] + [
                    parcel[p]["delivery_location_id"] for p in candidate
                ] + ["HUB"]
                distance = math.fsum(
                    distances[a][b] for a, b in zip(locations, locations[1:])
                )
                key = (change, distance, record["delivery_window_end"], pid, position)
                if best_key is None or key < best_key:
                    best_key = key
                    best_route = candidate
                    best_pid = pid

        if best_route is None:
            break
        route = two_opt(best_route, parcel, context)
        waiting.remove(best_pid)

    return route
