"""Shared route construction, improvement and dispatch rules."""
import math
from typing import Callable, Dict, List, Optional, Sequence

from simulator.models import Parcel, SimulationContext


DispatchPolicy = Callable[[Dict[str, Parcel], SimulationContext], List[str]]
PLANNING_INTERVAL = 10.0
UNDELIVERED_PENALTY = 240.0


def route_timing_penalty(route: List[str], parcel: Dict[str, Parcel],
                         context: SimulationContext) -> Optional[float]:
    """Return early + late minutes for a route, or None if it breaks range or cutoff."""
    distances = context["travel_distance"]
    departure_time = context["current_time"] + context["departure_delay"]
    location = "HUB"
    arrival_time = departure_time
    legs = []
    penalties = []
    # Drive the route in order, recording each leg and each stop's early/late minutes.
    for parcel_id in route:
        record = parcel[parcel_id]
        destination = record["delivery_location_id"]
        leg = distances[location][destination]
        legs.append(leg)
        # At 60 km/h, each kilometre takes one minute.
        arrival_time += leg
        penalties.append(max(0.0, record["delivery_window_start"] - arrival_time))
        penalties.append(max(0.0, arrival_time - record["delivery_window_end"]))
        location = destination

    # Reject routes whose round trip breaks the range limit or the return cutoff.
    trip_distance = math.fsum(legs + [distances[location]["HUB"]])
    if trip_distance > context["max_trip_distance_km"] + 1e-9:
        return None
    if departure_time + trip_distance > context["return_cutoff"]:
        return None
    return math.fsum(penalties)


def two_opt(route: List[str], parcel: Dict[str, Parcel],
            context: SimulationContext) -> List[str]:
    """Improve a starting route using the best feasible 2-opt reversal each round.

    The starting route is passed in, so any
    construction policy can reuse it.
    """
    def timing_penalty(candidate: List[str]) -> Optional[float]:
        return route_timing_penalty(candidate, parcel, context)

    # The starting route must itself be feasible.
    current_penalty = timing_penalty(route)
    if current_penalty is None:
        raise ValueError("Starting route is infeasible")

    # Best improvement: each round, try every segment reversal and keep the single best one.
    while True:
        best_route = route
        best_penalty = current_penalty
        for first in range(len(route)):
            for last in range(first + 1, len(route)):
                candidate = route.copy()
                # Reconnect the two boundary edges by reversing the enclosed segment.
                # Include full reversal: delivery timing can change even at equal distance.
                candidate[first:last + 1] = reversed(candidate[first:last + 1])
                penalty = timing_penalty(candidate)
                if penalty is not None and penalty < best_penalty - 1e-9:
                    best_route = candidate
                    best_penalty = penalty

        # Stop when no reversal lowers the penalty; otherwise apply the best and repeat.
        if best_route is route:
            return route
        route = best_route
        current_penalty = best_penalty


# Deadline and nearby route construction
def build_deadline_route(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Build a feasible route by deadline, then current distance, then parcel ID."""
    waiting = [
        parcel_id
        for parcel_id, record in parcel.items()
        if record["vehicle_assigned"] is None and record["delivery_time"] is None
    ]

    distances = context["travel_distance"]
    departure_time = context["current_time"] + context["departure_delay"]
    route: List[str] = []
    location = "HUB"
    load = 0.0
    travelled = 0.0

    while waiting:
        waiting.sort(key=lambda parcel_id: (
            parcel[parcel_id]["delivery_window_end"],
            distances[location][parcel[parcel_id]["delivery_location_id"]],
            parcel_id,
        ))
        for parcel_id in waiting:
            record = parcel[parcel_id]
            destination = record["delivery_location_id"]
            next_distance = travelled + distances[location][destination]
            round_trip_distance = next_distance + distances[destination]["HUB"]
            if load + record["size"] > context["capacity"] + 1e-9:
                continue
            if round_trip_distance > context["max_trip_distance_km"] + 1e-9:
                continue
            # At 60 km/h, each kilometre takes one minute.
            if departure_time + round_trip_distance > context["return_cutoff"]:
                continue

            route.append(parcel_id)
            waiting.remove(parcel_id)
            load += record["size"]
            travelled = next_distance
            location = destination
            break
        else:
            break  # No remaining parcel can be added to the current route.

    return route


def build_nearby_route(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Build a feasible route by current distance, then deadline, then parcel ID."""
    waiting = [
        parcel_id
        for parcel_id, record in parcel.items()
        if record["vehicle_assigned"] is None and record["delivery_time"] is None
    ]

    distances = context["travel_distance"]
    departure_time = context["current_time"] + context["departure_delay"]
    route: List[str] = []
    location = "HUB"
    load = 0.0
    travelled = 0.0

    while waiting:
        waiting.sort(key=lambda parcel_id: (
            distances[location][parcel[parcel_id]["delivery_location_id"]],
            parcel[parcel_id]["delivery_window_end"],
            parcel_id,
        ))
        for parcel_id in waiting:
            record = parcel[parcel_id]
            destination = record["delivery_location_id"]
            next_distance = travelled + distances[location][destination]
            round_trip_distance = next_distance + distances[destination]["HUB"]
            if load + record["size"] > context["capacity"] + 1e-9:
                continue
            if round_trip_distance > context["max_trip_distance_km"] + 1e-9:
                continue
            # At 60 km/h, each kilometre takes one minute.
            if departure_time + round_trip_distance > context["return_cutoff"]:
                continue

            route.append(parcel_id)
            waiting.remove(parcel_id)
            load += record["size"]
            travelled = next_distance
            location = destination
            break
        else:
            break  # No remaining parcel can be added to the current route.

    return route


# Deadline routes with local search
def build_deadline_two_opt(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Improve a deadline-first route using the best feasible 2-opt reversal each round."""
    route = build_deadline_route(parcel, context)
    return two_opt(route, parcel, context)


# Window-aligned departure
def build_window_aligned_route(parcel: Dict[str, Parcel], context: SimulationContext,
                               builder: DispatchPolicy = build_deadline_route) -> List[str]:
    """Defer an entirely early route one planning round when its return still fits.

    This uses only the currently constructed route. It does not predict future
    arrivals. Recompute normally at the next simulator planning round.
    """
    route = builder(parcel, context)
    if not route:
        return route
    distances = context["travel_distance"]
    departure = context["current_time"] + context["departure_delay"]
    arrival_time = departure
    location = "HUB"
    legs = []
    all_early = True
    for pid in route:
        record = parcel[pid]
        destination = record["delivery_location_id"]
        leg = distances[location][destination]
        legs.append(leg)
        arrival_time += leg
        if record["delivery_window_start"] - arrival_time < PLANNING_INTERVAL:
            all_early = False
        location = destination
    trip_distance = math.fsum(legs + [distances[location]["HUB"]])
    if all_early and departure + trip_distance + PLANNING_INTERVAL <= context["return_cutoff"]:
        return []
    return two_opt(route, parcel, context)


# Geographic selection experiment
def build_anchor_geo_route(parcel: Dict[str, Parcel], context: SimulationContext,
                           deadline_band: float) -> List[str]:
    """Keep the earliest feasible deadline as an anchor, then group nearby stops."""
    waiting = [pid for pid, record in parcel.items()
               if record["vehicle_assigned"] is None and record["delivery_time"] is None]
    distances = context["travel_distance"]
    departure = context["current_time"] + context["departure_delay"]
    route: List[str] = []
    anchor = None
    location = "HUB"
    load = 0.0
    travelled = 0.0

    while waiting:
        feasible = []
        for pid in waiting:
            record = parcel[pid]
            destination = record["delivery_location_id"]
            distance = travelled + distances[location][destination]
            round_trip = distance + distances[destination]["HUB"]
            if load + record["size"] > context["capacity"] + 1e-9:
                continue
            if round_trip > context["max_trip_distance_km"] + 1e-9:
                continue
            if departure + round_trip > context["return_cutoff"]:
                continue
            feasible.append(pid)
        if not feasible:
            break

        if anchor is None:
            chosen = min(feasible, key=lambda pid: (
                parcel[pid]["delivery_window_end"],
                distances[location][parcel[pid]["delivery_location_id"]], pid,
            ))
        else:
            earliest = min(parcel[pid]["delivery_window_end"] for pid in feasible)
            group = [pid for pid in feasible
                     if parcel[pid]["delivery_window_end"] <= earliest + deadline_band]
            chosen = min(group, key=lambda pid: (
                distances[anchor][parcel[pid]["delivery_location_id"]],
                distances[location][parcel[pid]["delivery_location_id"]],
                parcel[pid]["delivery_window_end"], pid,
            ))

        destination = parcel[chosen]["delivery_location_id"]
        route.append(chosen)
        waiting.remove(chosen)
        travelled += distances[location][destination]
        load += parcel[chosen]["size"]
        location = destination
        if anchor is None:
            anchor = destination
    return route


def make_anchor_geo_dispatch(deadline_band: float) -> DispatchPolicy:
    """Use geographic selection with the locked trip cap, waiting rule and 2-opt."""
    def construct(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
        return build_anchor_geo_route(parcel, context, deadline_band)

    def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
        departure = context["current_time"] + context["departure_delay"]
        limited = {**context, "return_cutoff": min(context["return_cutoff"], departure + 125.0)}
        return build_window_aligned_route(parcel, limited, builder=construct)

    return dispatch


# Urgency-share construction
def build_hybrid_route(parcel: Dict[str, Parcel], context: SimulationContext,
                urgent_share: float) -> List[str]:
    """Build a feasible route by deadline first, then by current distance.

    Stage 1 runs while load < urgent_share x capacity and sorts by deadline, then distance.
    Stage 2 sorts by distance, then deadline. urgent_share 0 matches nearby_first and
    urgent_share 1 matches deadline_first.
    """
    waiting = [
        parcel_id
        for parcel_id, record in parcel.items()
        if record["vehicle_assigned"] is None and record["delivery_time"] is None
    ]

    distances = context["travel_distance"]
    departure_time = context["current_time"] + context["departure_delay"]
    urgent_load = urgent_share * context["capacity"]
    route: List[str] = []
    location = "HUB"
    load = 0.0
    travelled = 0.0

    while waiting:
        if load < urgent_load:
            # Stage 1: most urgent deadline first.
            waiting.sort(key=lambda parcel_id: (
                parcel[parcel_id]["delivery_window_end"],
                distances[location][parcel[parcel_id]["delivery_location_id"]],
                parcel_id,
            ))
        else:
            # Stage 2: nearest parcel first.
            waiting.sort(key=lambda parcel_id: (
                distances[location][parcel[parcel_id]["delivery_location_id"]],
                parcel[parcel_id]["delivery_window_end"],
                parcel_id,
            ))
        for parcel_id in waiting:
            record = parcel[parcel_id]
            destination = record["delivery_location_id"]
            next_distance = travelled + distances[location][destination]
            round_trip_distance = next_distance + distances[destination]["HUB"]
            if load + record["size"] > context["capacity"] + 1e-9:
                continue
            if round_trip_distance > context["max_trip_distance_km"] + 1e-9:
                continue
            # At 60 km/h, each kilometre takes one minute.
            if departure_time + round_trip_distance > context["return_cutoff"]:
                continue

            route.append(parcel_id)
            waiting.remove(parcel_id)
            load += record["size"]
            travelled = next_distance
            location = destination
            break
        else:
            break  # No remaining parcel can be added to the current route.

    return route


def make_hybrid_dispatch(urgent_share: float, use_two_opt: bool = False) -> DispatchPolicy:
    """Build an urgency-share policy, optionally improving its route with 2-opt."""
    if not 0.0 <= urgent_share <= 1.0:
        raise ValueError("urgent_share must be between 0 and 1")

    def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
        route = build_hybrid_route(parcel, context, urgent_share)
        return two_opt(route, parcel, context) if use_two_opt else route

    return dispatch


# Candidate selection
def round_trip_km(route: List[str], parcel: Dict[str, Parcel],
                  context: SimulationContext) -> float:
    """Return hub -> stops in route order -> hub distance in km."""
    distances = context["travel_distance"]
    locations = ["HUB"] + [parcel[p]["delivery_location_id"] for p in route] + ["HUB"]
    return math.fsum(distances[a][b] for a, b in zip(locations, locations[1:]))


def make_candidate_dispatch(pool: Sequence[float], scoring: str) -> DispatchPolicy:
    """Return a dispatch that builds one 2-opt route per U in pool and keeps the lowest score.

    scoring "A": timing penalty - 240 x parcels.
    scoring "B": (timing penalty - 240 x parcels) / round-trip km.
    Ties keep the earlier U in pool.
    """
    if scoring not in ("A", "B"):
        raise ValueError('scoring must be "A" or "B"')
    if not pool:
        raise ValueError("pool must contain at least one U value")
    builders = [make_hybrid_dispatch(u) for u in pool]

    def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
        best_route: List[str] = []
        best_score = math.inf
        for build in builders:
            # Build the candidate, then improve it with 2-opt.
            route = build(parcel, context)
            if not route:
                continue  # skip empty candidates
            route = two_opt(route, parcel, context)
            penalty = route_timing_penalty(route, parcel, context)
            if penalty is None:
                continue  # cannot happen for feasible starts; kept as a safeguard
            score = penalty - UNDELIVERED_PENALTY * len(route)
            if scoring == "B":
                # Non-empty routes always have positive distance (all legs >= 3.03 km).
                score /= round_trip_km(route, parcel, context)
            # Strictly lower only, so ties keep the earlier U in the pool.
            if score < best_score:
                best_route = route
                best_score = score
        return best_route

    return dispatch


# Holding back future-window parcels
def make_holdback_dispatch(H: float, S: float = 30.0) -> DispatchPolicy:
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
        route = build_deadline_route(visible, context)
        return two_opt(route, visible, context)

    return dispatch


# Waiting for a fuller trip
def make_wait_to_fill_dispatch(F: float, max_wait: float = 30.0, urgent_margin: float = 30.0,
                  no_wait_after: float = 900.0) -> DispatchPolicy:
    """Return deadline-first + 2-opt that waits (returns []) while the van would leave under-filled.

    F: send once load >= F x capacity.
    max_wait: send once the van has been ready at the hub for this many minutes.
    urgent_margin: send if any parcel would arrive within this many minutes of its window end.
    no_wait_after: never wait at or after this time (minutes after midnight; 900 = 15:00).
    """

    def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
        # Same route as deadline_two_opt.
        route = build_deadline_route(parcel, context)
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


# Limiting route extension
def make_return_cap_dispatch(max_extension_minutes: float) -> Callable:
    """Limit 2-opt's return-time extension relative to the initial deadline route."""
    if not math.isfinite(max_extension_minutes) or max_extension_minutes < 0:
        raise ValueError("max_extension_minutes must be finite and non-negative")

    def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
        route = build_deadline_route(parcel, context)
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


# Morning fleet rules
def make_reserve(keep_idle: int, until: float = 600.0, urgent_within: float = 120.0) -> DispatchPolicy:
    """Before `until`, keep `keep_idle` vans at the hub unless the route has an urgent parcel.

    A parcel is urgent if its window closes within `urgent_within` minutes of departure.
    """
    def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
        route = build_window_aligned_route(parcel, context)
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
        return build_window_aligned_route(parcel, context)
    return dispatch
