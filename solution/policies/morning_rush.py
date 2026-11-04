"""Morning-rush variants built on deadline_window_departure.

Every morning, parcels arriving 08:00-10:00 with windows ending 10:00-11:00
are delivered late because all vans have already left on ~3-hour trips.
These variants keep fleet capacity available for that rush.
"""
from typing import Callable, Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.deadline_window_departure import dispatch as window_dispatch

DispatchPolicy = Callable[[Dict[str, Parcel], SimulationContext], List[str]]


def make_reserve(keep_idle: int, until: float = 600.0, urgent_within: float = 120.0) -> DispatchPolicy:
    """Before `until`, keep `keep_idle` vans at the hub unless the route has an urgent parcel.

    A parcel is urgent if its window closes within `urgent_within` minutes of departure.
    """
    def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
        route = window_dispatch(parcel, context)
        now = context["current_time"]
        if not route or now >= until:
            return route
        departure = now + context["departure_delay"]
        if any(parcel[pid]["delivery_window_end"] - departure <= urgent_within for pid in route):
            return route
        idle = sum(1 for v in context["fleet"].values() if v["available_at"] <= now)
        # `idle` includes this van; sending it leaves idle - 1 at the hub.
        return route if idle - 1 >= keep_idle else []
    return dispatch


def make_morning_cap(before: float, return_by: float) -> DispatchPolicy:
    """Trips planned before `before` must be back at the hub by `return_by`."""
    def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
        if context["current_time"] < before:
            context = {**context, "return_cutoff": min(context["return_cutoff"], return_by)}
        return window_dispatch(parcel, context)
    return dispatch
