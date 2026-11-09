"""Reproduce the reported 115-minute trip-limit setting."""
from solution.policies.helpers import build_window_aligned_route as window_dispatch


def dispatch(parcel, context):
    departure = context["current_time"] + context["departure_delay"]
    limited = {**context, "return_cutoff": min(context["return_cutoff"], departure + 115.0)}
    return window_dispatch(parcel, limited)
