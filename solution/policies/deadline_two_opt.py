from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.helpers import build_deadline_two_opt


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Improve a deadline-first route using the best feasible 2-opt reversal each round."""
    return build_deadline_two_opt(parcel, context)
