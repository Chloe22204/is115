import math
from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.deadline_two_opt import dispatch as initial_dispatch
from solution.policies.helpers import route_timing_penalty, two_opt


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Alternate best single-parcel relocations with 2-opt, keeping selections fixed."""
    route = initial_dispatch(parcel, context)
    distances = context["travel_distance"]
    while len(route) > 1:
        current_penalty = route_timing_penalty(route, parcel, context)
        if current_penalty is None:
            raise ValueError("Starting route is infeasible")
        best_key = None
        best_route = None
        for source, pid in enumerate(route):
            remaining = route[:source] + route[source + 1:]
            for position in range(len(remaining) + 1):
                if position == source:
                    continue
                candidate = remaining[:position] + [pid] + remaining[position:]
                penalty = route_timing_penalty(candidate, parcel, context)
                if penalty is None or penalty >= current_penalty - 1e-9:
                    continue
                locations = ["HUB"] + [
                    parcel[p]["delivery_location_id"] for p in candidate
                ] + ["HUB"]
                distance = math.fsum(
                    distances[a][b] for a, b in zip(locations, locations[1:])
                )
                key = (penalty, distance, pid, position)
                if best_key is None or key < best_key:
                    best_key = key
                    best_route = candidate
        if best_route is None:
            break
        route = two_opt(best_route, parcel, context)
    return route
