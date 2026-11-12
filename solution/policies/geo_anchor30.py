"""Geographic grouping within 30 minutes of the earliest feasible deadline."""
from solution.policies.helpers import make_anchor_geo_dispatch

dispatch = make_anchor_geo_dispatch(30.0)
