from typing import Dict, List

from simulator.models import Parcel, SimulationContext


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Build a feasible route by deadline, then current distance, then parcel ID."""
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
            parcel[parcel_id]["delivery_window_end"],
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
