from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.helpers import build_window_aligned_route as window_dispatch


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Limit travel to 125 minutes while checking hub waiting against 18:00."""
    # At 60 km/h, a kilometre limit equals a travel-minute limit.
    limited = {**context, "max_trip_distance_km": min(context["max_trip_distance_km"], 125.0)}
    return window_dispatch(parcel, limited)
