from solution.policies.helpers import make_cluster_dispatch

# Seed-and-cluster (nearest to any route stop, 60-min tolerance) only before 10:00;
# plain deadline_trip_limit construction from 10:00 onwards. X chosen on days 1-10.
dispatch = make_cluster_dispatch(tolerance=60.0, measure="route", cluster_before=600.0)
