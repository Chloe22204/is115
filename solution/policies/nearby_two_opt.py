from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.helpers import build_nearby_route, two_opt


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Improve a nearby-first route using the best feasible 2-opt reversal each round."""
    route = build_nearby_route(parcel, context)
    return two_opt(route, parcel, context)
