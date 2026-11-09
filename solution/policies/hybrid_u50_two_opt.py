"""Hybrid urgent/nearby policy with urgent_share = 0.5 with 2-opt improvement."""
from solution.policies.helpers import make_hybrid_dispatch as make_dispatch

dispatch = make_dispatch(0.5, use_two_opt=True)
