import math
from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.helpers import two_opt

PLANNING_INTERVAL = 10.0


def _build_route(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Build by deadline minus projected arrival, then current distance and ID."""
    waiting = [
        parcel_id
        for parcel_id, record in parcel.items()
        if record["vehicle_assigned"] is None and record["delivery_time"] is None
    ]

    distances = context["travel_distance"]
    departure_time = context["current_time"] + context["departure_delay"]
    route: List[str] = []
    location = "HUB"
    load = 0.0
    travelled = 0.0

    while waiting:
        waiting.sort(key=lambda parcel_id: (
            parcel[parcel_id]["delivery_window_end"] - (
                departure_time + travelled
                + distances[location][parcel[parcel_id]["delivery_location_id"]]
            ),
            distances[location][parcel[parcel_id]["delivery_location_id"]],
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


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Least-slack selection with the existing 125-minute cap, waiting and 2-opt."""
    departure = context["current_time"] + context["departure_delay"]
    context = {**context, "return_cutoff": min(context["return_cutoff"], departure + 125.0)}
    route = _build_route(parcel, context)
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
    return two_opt(route, parcel, context)
