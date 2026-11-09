from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.helpers import build_nearby_route


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Build a feasible route by current distance, then deadline, then parcel ID."""
    return build_nearby_route(parcel, context)
