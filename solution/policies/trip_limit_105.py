"""Reproduce the reported 105-minute trip-limit setting."""
from solution.policies.deadline_window_departure import dispatch as window_dispatch


def dispatch(parcel, context):
    departure = context["current_time"] + context["departure_delay"]
    limited = {**context, "return_cutoff": min(context["return_cutoff"], departure + 105.0)}
    return window_dispatch(parcel, limited)
