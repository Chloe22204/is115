"""Wait-to-fill deadline-first + 2-opt with F = 0.9."""
from solution.policies.wait_to_fill import make_dispatch

dispatch = make_dispatch(0.9)
