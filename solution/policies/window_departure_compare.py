from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.helpers import (
    build_deadline_route as deadline_dispatch,
    route_timing_penalty,
    two_opt,
)

PLANNING_INTERVAL = 10.0


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Wait one planning round when leaving later would lower the route's timing penalty.

    Builds the deadline-first route, improves it with 2-opt, then compares its
    early + late minutes if it departs now versus one planning round later.
    Waits only if the later departure is still feasible and strictly better.
    """
    route = deadline_dispatch(parcel, context)
    if not route:
        return route
    route = two_opt(route, parcel, context)
    now_penalty = route_timing_penalty(route, parcel, context)
    later_context = dict(context)
    later_context["current_time"] = context["current_time"] + PLANNING_INTERVAL
    later_penalty = route_timing_penalty(route, parcel, later_context)
    if later_penalty is not None and later_penalty < now_penalty - 1e-9:
        return []
    return route
