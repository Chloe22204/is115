from solution.policies.morning_rush import make_morning_cap

# Trips planned before 10:00 must be back at the hub by 10:15, so vans are
# free for the 08:00-10:00 arrivals whose windows close at 10:00-11:00.
dispatch = make_morning_cap(before=600.0, return_by=615.0)
