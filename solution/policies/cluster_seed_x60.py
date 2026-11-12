from solution.policies.helpers import make_cluster_dispatch

# Seed-and-cluster: pool = window end within 60 min of the seed, nearest to the seed first.
dispatch = make_cluster_dispatch(tolerance=60.0, measure="seed")
