"""Hold-back deadline-first + 2-opt with H = 60 minutes."""
from solution.policies.holdback_two_opt import make_dispatch

dispatch = make_dispatch(60)
