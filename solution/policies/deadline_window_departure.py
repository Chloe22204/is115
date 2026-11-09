from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.helpers import build_window_aligned_route


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Defer an entirely early route one planning round when its return still fits."""
    return build_window_aligned_route(parcel, context)
