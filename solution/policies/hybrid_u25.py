"""Hybrid urgent/nearby policy with urgent_share = 0.25."""
from solution.policies.hybrid_urgent_nearby import make_dispatch

dispatch = make_dispatch(0.25)
