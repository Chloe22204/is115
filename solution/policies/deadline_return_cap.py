import math
from typing import Callable, Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.deadline_first import dispatch as deadline_dispatch
from solution.policies.two_opt_helper import two_opt


def make_dispatch(max_extension_minutes: float) -> Callable:
    """Limit 2-opt's return-time extension relative to the initial deadline route."""
    if not math.isfinite(max_extension_minutes) or max_extension_minutes < 0:
        raise ValueError("max_extension_minutes must be finite and non-negative")

    def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
        route = deadline_dispatch(parcel, context)
        if not route:
            return route

        locations = ["HUB"] + [parcel[pid]["delivery_location_id"] for pid in route] + ["HUB"]
        distances = context["travel_distance"]
        original_distance = math.fsum(
            distances[origin][destination]
            for origin, destination in zip(locations, locations[1:])
        )
        departure = context["current_time"] + context["departure_delay"]
        # At 60 km/h, the initial distance also gives the initial driving minutes.
        latest_return = departure + original_distance + max_extension_minutes
        limited_context = {
            **context,
            "return_cutoff": min(context["return_cutoff"], latest_return),
        }
        return two_opt(route, parcel, limited_context)

    return dispatch
