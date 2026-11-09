from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.helpers import build_window_aligned_route as window_dispatch

# Longest a trip may last, from hub departure to return, in minutes.
# 105-130 all score well on the supplied days; 100 and below or 135 and above
# score much worse (see docs/trip_limit_experiment.md).
MAX_TRIP_MINUTES = 125.0


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """deadline_window_departure with every trip limited to MAX_TRIP_MINUTES.

    Short trips bring vans back to the hub often, so parcels that arrive while
    the fleet is out (notably the 08:00-10:00 rush due by 10:00-11:00) wait less.
    """
    departure = context["current_time"] + context["departure_delay"]
    limited = {**context, "return_cutoff": min(context["return_cutoff"], departure + MAX_TRIP_MINUTES)}
    return window_dispatch(parcel, limited)
