"""Hybrid urgent/nearby policy with urgent_share = 1.0 with 2-opt improvement."""
from solution.policies.hybrid_urgent_nearby import make_dispatch

dispatch = make_dispatch(1.0, two_opt=True)
