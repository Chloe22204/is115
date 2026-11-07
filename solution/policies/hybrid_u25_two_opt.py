"""Hybrid urgent/nearby policy with urgent_share = 0.25 with 2-opt improvement."""
from solution.policies.hybrid_urgent_nearby import make_dispatch

dispatch = make_dispatch(0.25, two_opt=True)
