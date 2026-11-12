"""Geographic grouping within 60 minutes of the earliest feasible deadline."""
from solution.policies.helpers import make_anchor_geo_dispatch

dispatch = make_anchor_geo_dispatch(60.0)
