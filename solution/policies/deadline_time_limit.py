from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.deadline_window_departure import dispatch as window_dispatch

MORNING_END = 10 * 60.0
MORNING_LIMIT = 110.0
LATER_LIMIT = 125.0


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Use 110-minute trips before the 10:00 planning round, then 125 minutes."""
    now = context["current_time"]
    trip_limit = MORNING_LIMIT if now < MORNING_END else LATER_LIMIT
    departure = now + context["departure_delay"]
    limited = {**context, "return_cutoff": min(context["return_cutoff"], departure + trip_limit)}
    return window_dispatch(parcel, limited)
