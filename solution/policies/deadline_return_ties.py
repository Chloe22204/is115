import math
from typing import Dict, List, Optional

from simulator.models import Parcel, SimulationContext
from solution.policies.helpers import (
    build_deadline_route as deadline_dispatch,
    route_timing_penalty,
)

PLANNING_INTERVAL = 10.0


def _trip_distance(route: List[str], parcel: Dict[str, Parcel],
                   context: SimulationContext) -> float:
    locations = ["HUB"] + [parcel[pid]["delivery_location_id"] for pid in route] + ["HUB"]
    distances = context["travel_distance"]
    return math.fsum(distances[a][b] for a, b in zip(locations, locations[1:]))


def _two_opt_return_ties(route: List[str], parcel: Dict[str, Parcel],
            context: SimulationContext) -> List[str]:
    """Prefer a shorter trip only when the timing penalty is exactly equal."""
    def timing_penalty(candidate: List[str]) -> Optional[float]:
        return route_timing_penalty(candidate, parcel, context)

    # The starting route must itself be feasible.
    current_penalty = timing_penalty(route)
    if current_penalty is None:
        raise ValueError("Starting route is infeasible")

    current_distance = _trip_distance(route, parcel, context)

    # Keep timing primary; exact ties may reduce the time away from the hub.
    while True:
        best_route = route
        best_penalty = current_penalty
        best_distance = current_distance
        for first in range(len(route)):
            for last in range(first + 1, len(route)):
                candidate = route.copy()
                # Reconnect the two boundary edges by reversing the enclosed segment.
                # Include full reversal: delivery timing can change even at equal distance.
                candidate[first:last + 1] = reversed(candidate[first:last + 1])
                penalty = timing_penalty(candidate)
                if penalty is None:
                    continue
                distance = _trip_distance(candidate, parcel, context)
                if penalty < best_penalty - 1e-9 or (
                    penalty == best_penalty and distance < best_distance - 1e-9
                ):
                    best_route = candidate
                    best_penalty = penalty
                    best_distance = distance

        # Stop when no reversal lowers the penalty; otherwise apply the best and repeat.
        if best_route is route:
            return route
        route = best_route
        current_penalty = best_penalty
        current_distance = best_distance


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Use deadline-first and 125-minute trips with a return-time tie-break."""
    departure = context["current_time"] + context["departure_delay"]
    context = {**context, "return_cutoff": min(context["return_cutoff"], departure + 125.0)}
    route = deadline_dispatch(parcel, context)
    if not route:
        return route
    distances = context["travel_distance"]
    departure = context["current_time"] + context["departure_delay"]
    arrival_time = departure
    location = "HUB"
    legs = []
    all_early = True
    for pid in route:
        record = parcel[pid]
        destination = record["delivery_location_id"]
        leg = distances[location][destination]
        legs.append(leg)
        arrival_time += leg
        if record["delivery_window_start"] - arrival_time < PLANNING_INTERVAL:
            all_early = False
        location = destination
    trip_distance = math.fsum(legs + [distances[location]["HUB"]])
    if all_early and departure + trip_distance + PLANNING_INTERVAL <= context["return_cutoff"]:
        return []
    return _two_opt_return_ties(route, parcel, context)
