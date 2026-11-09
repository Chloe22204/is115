"""Default urgency-share policy. Shared construction is in helpers.py."""
from solution.policies.helpers import (
    build_hybrid_route as build_route,
    make_hybrid_dispatch as make_dispatch,
)

DEFAULT_URGENT_SHARE = 0.5

dispatch = make_dispatch(DEFAULT_URGENT_SHARE)
