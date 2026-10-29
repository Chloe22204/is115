import math
from typing import Dict, List, Optional

from simulator.models import Parcel, SimulationContext


def route_timing_penalty(route: List[str], parcel: Dict[str, Parcel],
                         context: SimulationContext) -> Optional[float]:
    """Return early + late minutes for a route, or None if it breaks range or cutoff."""
    distances = context["travel_distance"]
    departure_time = context["current_time"] + context["departure_delay"]
    location = "HUB"
    arrival_time = departure_time
    legs = []
    penalties = []
    # Drive the route in order, recording each leg and each stop's early/late minutes.
    for parcel_id in route:
        record = parcel[parcel_id]
        destination = record["delivery_location_id"]
        leg = distances[location][destination]
        legs.append(leg)
        # At 60 km/h, each kilometre takes one minute.
        arrival_time += leg
        penalties.append(max(0.0, record["delivery_window_start"] - arrival_time))
        penalties.append(max(0.0, arrival_time - record["delivery_window_end"]))
        location = destination

    # Reject routes whose round trip breaks the range limit or the return cutoff.
    trip_distance = math.fsum(legs + [distances[location]["HUB"]])
    if trip_distance > context["max_trip_distance_km"] + 1e-9:
        return None
    if departure_time + trip_distance > context["return_cutoff"]:
        return None
    return math.fsum(penalties)


def two_opt(route: List[str], parcel: Dict[str, Parcel],
            context: SimulationContext) -> List[str]:
    """Improve a starting route using the best feasible 2-opt reversal each round.

    Same rule as nearby_two_opt.py, but the starting route is passed in, so any
    construction policy can reuse it.
    """
    def timing_penalty(candidate: List[str]) -> Optional[float]:
        return route_timing_penalty(candidate, parcel, context)

    # The starting route must itself be feasible.
    current_penalty = timing_penalty(route)
    if current_penalty is None:
        raise ValueError("Starting route is infeasible")

    # Best improvement: each round, try every segment reversal and keep the single best one.
    while True:
        best_route = route
        best_penalty = current_penalty
        for first in range(len(route)):
            for last in range(first + 1, len(route)):
                candidate = route.copy()
                # Reconnect the two boundary edges by reversing the enclosed segment.
                # Include full reversal: delivery timing can change even at equal distance.
                candidate[first:last + 1] = reversed(candidate[first:last + 1])
                penalty = timing_penalty(candidate)
                if penalty is not None and penalty < best_penalty - 1e-9:
                    best_route = candidate
                    best_penalty = penalty

        # Stop when no reversal lowers the penalty; otherwise apply the best and repeat.
        if best_route is route:
            return route
        route = best_route
        current_penalty = best_penalty
