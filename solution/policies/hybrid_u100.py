"""Hybrid urgent/nearby policy with urgent_share = 1.0."""
from solution.policies.helpers import make_hybrid_dispatch as make_dispatch

dispatch = make_dispatch(1.0)
