from typing import Callable, Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies import nearby_two_opt

# Fraction of capacity filled by deadline order before switching to distance order.
# Wrapper modules (hybrid_u25.py etc.) set their own value via make_dispatch.
DEFAULT_URGENT_SHARE = 0.5

DispatchPolicy = Callable[[Dict[str, Parcel], SimulationContext], List[str]]


def build_route(parcel: Dict[str, Parcel], context: SimulationContext,
                urgent_share: float) -> List[str]:
    """Build a feasible route by deadline first, then by current distance.

    Stage 1 runs while load < urgent_share x capacity and sorts by deadline, then distance.
    Stage 2 sorts by distance, then deadline. urgent_share 0 matches nearby_first and
    urgent_share 1 matches deadline_first.
    """
    waiting = [
        parcel_id
        for parcel_id, record in parcel.items()
        if record["vehicle_assigned"] is None and record["delivery_time"] is None
    ]

    distances = context["travel_distance"]
    departure_time = context["current_time"] + context["departure_delay"]
    urgent_load = urgent_share * context["capacity"]
    route: List[str] = []
    location = "HUB"
    load = 0.0
    travelled = 0.0

    while waiting:
        if load < urgent_load:
            # Stage 1: most urgent deadline first.
            waiting.sort(key=lambda parcel_id: (
                parcel[parcel_id]["delivery_window_end"],
                distances[location][parcel[parcel_id]["delivery_location_id"]],
                parcel_id,
            ))
        else:
            # Stage 2: nearest parcel first.
            waiting.sort(key=lambda parcel_id: (
                distances[location][parcel[parcel_id]["delivery_location_id"]],
                parcel[parcel_id]["delivery_window_end"],
                parcel_id,
            ))
        for parcel_id in waiting:
            record = parcel[parcel_id]
            destination = record["delivery_location_id"]
            next_distance = travelled + distances[location][destination]
            round_trip_distance = next_distance + distances[destination]["HUB"]
            if load + record["size"] > context["capacity"] + 1e-9:
                continue
            if round_trip_distance > context["max_trip_distance_km"] + 1e-9:
                continue
            # At 60 km/h, each kilometre takes one minute.
            if departure_time + round_trip_distance > context["return_cutoff"]:
                continue

            route.append(parcel_id)
            waiting.remove(parcel_id)
            load += record["size"]
            travelled = next_distance
            location = destination
            break
        else:
            break  # No remaining parcel can be added to the current route.

    return route


def make_dispatch(urgent_share: float, two_opt: bool = False) -> DispatchPolicy:
    """Return a dispatch function for a fixed urgent_share, optionally improved by 2-opt."""
    if not 0.0 <= urgent_share <= 1.0:
        raise ValueError("urgent_share must be between 0 and 1")

    def hybrid_dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
        return build_route(parcel, context, urgent_share)

    if not two_opt:
        return hybrid_dispatch

    def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
        # Reuse nearby_two_opt's improvement loop unchanged by swapping in the hybrid
        # route as its starting route for this one call, then restoring the original.
        original = nearby_two_opt.nearby_dispatch
        nearby_two_opt.nearby_dispatch = hybrid_dispatch
        try:
            return nearby_two_opt.dispatch(parcel, context)
        finally:
            nearby_two_opt.nearby_dispatch = original

    return dispatch


dispatch = make_dispatch(DEFAULT_URGENT_SHARE)
