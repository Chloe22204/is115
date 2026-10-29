import math
from typing import Callable, Dict, List, Sequence

from simulator.models import Parcel, SimulationContext
from solution.policies.hybrid_urgent_nearby import make_dispatch as make_hybrid
from solution.policies.two_opt_helper import route_timing_penalty, two_opt

UNDELIVERED_PENALTY = 240.0  # credit per parcel carried, matching the main metric

DispatchPolicy = Callable[[Dict[str, Parcel], SimulationContext], List[str]]


def round_trip_km(route: List[str], parcel: Dict[str, Parcel],
                  context: SimulationContext) -> float:
    """Return hub -> stops in route order -> hub distance in km."""
    distances = context["travel_distance"]
    locations = ["HUB"] + [parcel[p]["delivery_location_id"] for p in route] + ["HUB"]
    return math.fsum(distances[a][b] for a, b in zip(locations, locations[1:]))


def make_dispatch(pool: Sequence[float], scoring: str) -> DispatchPolicy:
    """Return a dispatch that builds one 2-opt route per U in pool and keeps the lowest score.

    scoring "A": timing penalty - 240 x parcels.
    scoring "B": (timing penalty - 240 x parcels) / round-trip km.
    Ties keep the earlier U in pool.
    """
    if scoring not in ("A", "B"):
        raise ValueError('scoring must be "A" or "B"')
    if not pool:
        raise ValueError("pool must contain at least one U value")
    builders = [make_hybrid(u) for u in pool]

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
