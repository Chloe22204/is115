from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.deadline_window_departure import dispatch as window_dispatch


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Use a 110-minute trip limit with at most two idle vans, otherwise 125."""
    now = context["current_time"]
    idle = sum(vehicle["available_at"] <= now for vehicle in context["fleet"].values())
    trip_limit = 110.0 if idle <= 2 else 125.0
    departure = now + context["departure_delay"]
    limited = {**context, "return_cutoff": min(context["return_cutoff"], departure + trip_limit)}
    return window_dispatch(parcel, limited)
