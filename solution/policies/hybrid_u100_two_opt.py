"""Hybrid urgent/nearby policy with urgent_share = 1.0 with 2-opt improvement."""
from solution.policies.helpers import make_hybrid_dispatch as make_dispatch

dispatch = make_dispatch(1.0, use_two_opt=True)
