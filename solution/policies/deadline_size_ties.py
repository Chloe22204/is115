from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.helpers import two_opt


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Use smaller size only after deadline and distance ties; then apply 2-opt."""
    waiting = [
        pid for pid, record in parcel.items()
        if record["vehicle_assigned"] is None and record["delivery_time"] is None
    ]
    distances = context["travel_distance"]
    departure = context["current_time"] + context["departure_delay"]
    route: List[str] = []
    location = "HUB"
    load = 0.0
    travelled = 0.0
    while waiting:
        waiting.sort(key=lambda pid: (
            parcel[pid]["delivery_window_end"],
            distances[location][parcel[pid]["delivery_location_id"]],
            parcel[pid]["size"],
            pid,
        ))
        for pid in waiting:
            record = parcel[pid]
            destination = record["delivery_location_id"]
            next_distance = travelled + distances[location][destination]
            round_trip = next_distance + distances[destination]["HUB"]
            if load + record["size"] > context["capacity"] + 1e-9:
                continue
            if round_trip > context["max_trip_distance_km"] + 1e-9:
                continue
            if departure + round_trip > context["return_cutoff"]:
                continue
            route.append(pid)
            waiting.remove(pid)
            load += record["size"]
            travelled = next_distance
            location = destination
            break
        else:
            break
    return two_opt(route, parcel, context)
