"""Hold-back deadline-first + 2-opt with H = 120 minutes."""
from solution.policies.helpers import make_holdback_dispatch as make_dispatch

dispatch = make_dispatch(120)
