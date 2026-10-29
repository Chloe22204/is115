from typing import Callable, Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.deadline_first import dispatch as deadline_dispatch
from solution.policies.two_opt_helper import two_opt

DispatchPolicy = Callable[[Dict[str, Parcel], SimulationContext], List[str]]


def make_dispatch(H: float, S: float = 30.0) -> DispatchPolicy:
    """Return deadline-first + 2-opt that holds back parcels whose window opens much later.

    H: minutes the window may open after the van's direct arrival before the parcel is held.
    S: safety margin in minutes before the return cutoff for sending a held parcel later.
    """

    def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
        distances = context["travel_distance"]
        departure = context["current_time"] + context["departure_delay"]
        latest_return = context["return_cutoff"] - S

        # Decide which waiting parcels to hold back for this call.
        held = set()
        for parcel_id, record in parcel.items():
            if record["vehicle_assigned"] is not None or record["delivery_time"] is not None:
                continue  # not waiting
            location = record["delivery_location_id"]
            d = distances["HUB"][location]
            est_arrival = departure + d  # direct hub -> parcel, 1 km = 1 minute
            window_start = record["delivery_window_start"]
            # a) the window opens more than H minutes after the van would arrive
            too_early = window_start - est_arrival > H
            # b) a later direct trip, leaving H minutes before the window, is back by cutoff - S
            later_departure = window_start - H - d
            can_send_later = later_departure + (d + distances[location]["HUB"]) <= latest_return
            if too_early and can_send_later:
                held.add(parcel_id)

        # New dict without the held parcels; the snapshot itself is not changed.
        visible = {pid: rec for pid, rec in parcel.items() if pid not in held}

        # Deadline-first route on the visible parcels, then 2-opt with the same dict.
        route = deadline_dispatch(visible, context)
        return two_opt(route, visible, context)

    return dispatch
