from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.deadline_window_departure import dispatch as window_dispatch


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Use fleet-aware travel limits while checking hub waiting against 18:00."""
    now = context["current_time"]
    idle = sum(vehicle["available_at"] <= now for vehicle in context["fleet"].values())
    trip_limit = 110.0 if idle <= 2 else 125.0
    # Keep the physical return cutoff separate from the travel allowance.
    limited = {**context, "max_trip_distance_km": min(context["max_trip_distance_km"], trip_limit)}
    return window_dispatch(parcel, limited)
