from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.deadline_first import dispatch as deadline_dispatch
from solution.policies.two_opt_helper import two_opt


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Improve a deadline-first route using the best feasible 2-opt reversal each round."""
    route = deadline_dispatch(parcel, context)
    return two_opt(route, parcel, context)
