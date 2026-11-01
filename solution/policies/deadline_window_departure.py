import math
from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.deadline_first import dispatch as deadline_dispatch
from solution.policies.two_opt_helper import two_opt

PLANNING_INTERVAL = 10.0


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Defer an entirely early route one planning round when its return still fits.

    This uses only the currently constructed route. It does not predict future
    arrivals. Recompute normally at the next simulator planning round.
    """
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
    return two_opt(route, parcel, context)
