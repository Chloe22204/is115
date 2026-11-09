from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.helpers import build_deadline_route


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Build a feasible route by deadline, then current distance, then parcel ID."""
    return build_deadline_route(parcel, context)
