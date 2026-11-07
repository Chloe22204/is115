"""Candidate selection with pool [1, 0.75, 0.5, 0.25, 0] and scoring B."""
from solution.policies.candidate_selection import make_dispatch

dispatch = make_dispatch([1, 0.75, 0.5, 0.25, 0], "B")
