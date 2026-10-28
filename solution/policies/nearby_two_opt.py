import math
from typing import Dict, List, Optional

from simulator.models import Parcel, SimulationContext
from solution.policies.nearby_first import dispatch as nearby_dispatch


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Improve a nearby-first route using the best feasible 2-opt reversal each round."""
    route = nearby_dispatch(parcel, context)
    distances = context["travel_distance"]
    departure_time = context["current_time"] + context["departure_delay"]

    def timing_penalty(candidate: List[str]) -> Optional[float]:
        location = "HUB"
        arrival_time = departure_time
        legs = []
        penalties = []
        for parcel_id in candidate:
            record = parcel[parcel_id]
            destination = record["delivery_location_id"]
            leg = distances[location][destination]
            legs.append(leg)
            # At 60 km/h, each kilometre takes one minute.
            arrival_time += leg
            penalties.append(max(0.0, record["delivery_window_start"] - arrival_time))
            penalties.append(max(0.0, arrival_time - record["delivery_window_end"]))
            location = destination

        trip_distance = math.fsum(legs + [distances[location]["HUB"]])
        if trip_distance > context["max_trip_distance_km"] + 1e-9:
            return None
        if departure_time + trip_distance > context["return_cutoff"]:
            return None
        return math.fsum(penalties)

    current_penalty = timing_penalty(route)
    if current_penalty is None:
        raise ValueError("Nearby-first produced an infeasible initial route")

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

        if best_route is route:
            return route
        route = best_route
        current_penalty = best_penalty
