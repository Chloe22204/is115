import math
from typing import Callable, Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.deadline_first import dispatch as deadline_dispatch
from solution.policies.two_opt_helper import two_opt

DispatchPolicy = Callable[[Dict[str, Parcel], SimulationContext], List[str]]


def make_dispatch(F: float, max_wait: float = 30.0, urgent_margin: float = 30.0,
                  no_wait_after: float = 900.0) -> DispatchPolicy:
    """Return deadline-first + 2-opt that waits (returns []) while the van would leave under-filled.

    F: send once load >= F x capacity.
    max_wait: send once the van has been ready at the hub for this many minutes.
    urgent_margin: send if any parcel would arrive within this many minutes of its window end.
    no_wait_after: never wait at or after this time (minutes after midnight; 900 = 15:00).
    """

    def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
        # Same route as deadline_two_opt.
        route = deadline_dispatch(parcel, context)
        route = two_opt(route, parcel, context)
        if not route:
            return route

        # Load and estimated delivery times, following the route from the hub (1 km = 1 minute).
        load = math.fsum(parcel[p]["size"] for p in route)
        distances = context["travel_distance"]
        time = context["current_time"] + context["departure_delay"]
        location = "HUB"
        urgent = False
        for parcel_id in route:
            record = parcel[parcel_id]
            time += distances[location][record["delivery_location_id"]]
            location = record["delivery_location_id"]
            if record["delivery_window_end"] - time < urgent_margin:
                urgent = True

        # Send now if any condition holds; otherwise wait for the next 10-minute call.
        waited = context["current_time"] - context["fleet"][context["vehicle_id"]]["available_at"]
        if (load >= F * context["capacity"]                 # a) full enough
                or urgent                                   # b) a parcel is close to its deadline
                or waited >= max_wait                       # c) waited long enough
                or context["current_time"] >= no_wait_after):  # d) too late in the day to wait
            return route
        return []

    return dispatch
