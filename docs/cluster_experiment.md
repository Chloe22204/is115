# Seed-and-cluster construction: negative result

**Decision: not adopted. `deadline_trip_limit` stays the submitted policy.** No variant meets the adoption rule set before the runs. The rule required a lower penalty on at least 16 of 20 days, plus a held-out (days 11–20) improvement of at least 2% with no worse total.

## What was tried

Code: `build_cluster_route`, `wait_or_two_opt` and `make_cluster_dispatch` in `solution/policies/helpers.py`, plus one module per variant. Everything else is identical to `deadline_trip_limit`: the 125-minute trip cap, the all-early departure wait, and 2-opt.

1. **Seed:** the parcel `deadline_first` would pick first. That is the earliest window end, ties broken by hub distance and then parcel ID, among parcels that fit as a one-stop trip.
2. **Pool:** waiting parcels whose window end is at most X minutes after the seed's.
3. **Order:** pool parcels are added nearest first, then by window end, then by ID. "Nearest" means distance to the seed (`seed` variants) or to the closest stop already in the route (`route` variants).
4. **Feasibility:** each parcel is inserted at its cheapest position. It is kept only if capacity, the 320 km range and the return cutoff (including the 125-minute cap) all still hold.
5. **Finish:** the departure wait rule, then 2-opt.

Variants: X ∈ {60, 120, 240} for each distance measure. A morning-only variant (`cluster_morning_route_x60`) clusters only before 10:00 and uses plain `deadline_trip_limit` construction afterwards. Its settings (route measure, X = 60) were chosen on days 1–10 only. X = 60 and X = 120 tied there, and the smaller value was taken.

## Results (20 days, `results/<variant>/`)

| Variant | Delivered | Undelivered | Early min | Late min | Total penalty | vs best | Days W/L/T | Days 11–20 W/L | Days 11–20 change |
|---|---:|---:|---:|---:|---:|---:|:-:|:-:|---:|
| `deadline_trip_limit` (current best) | 15,222 | 645 | 447.91 | 23,840.78 | 179,088.70 | — | — | — | — |
| `cluster_seed_x60` | 15,190 | 677 | 742.47 | 24,789.28 | 188,011.80 | +4.98% | 1/19/0 | 1/9 | +5.71% |
| `cluster_seed_x120` | 15,190 | 677 | 742.47 | 24,789.28 | 188,011.80 | +4.98% | 1/19/0 | 1/9 | +5.71% |
| `cluster_seed_x240` | 15,204 | 663 | 739.06 | 28,552.81 | 188,411.91 | +5.21% | 2/18/0 | 2/8 | +6.11% |
| `cluster_route_x60` | 15,218 | 649 | 863.42 | 23,363.85 | 179,987.27 | +0.50% | 8/11/1 | 5/5 | +0.40% |
| `cluster_route_x120` | 15,218 | 649 | 863.42 | 23,363.85 | 179,987.27 | +0.50% | 8/11/1 | 5/5 | +0.40% |
| `cluster_route_x240` | 15,222 | 645 | 881.67 | 25,491.08 | 181,172.79 | +1.16% | 8/11/1 | 4/6 | +1.63% |
| `cluster_morning_route_x60` | 15,225 | 642 | 422.91 | 23,530.78 | **178,033.69** | **−0.59%** | 5/0/15 | 3/0 | −0.29% |

Split halves (penalty):

| Variant | Days 1–10 (tuning) | Days 11–20 (held out) |
|---|---:|---:|
| `deadline_trip_limit` | 90,383.74 | 88,704.96 |
| `cluster_route_x60` | 90,930.66 | 89,056.61 |
| `cluster_morning_route_x60` | 89,586.46 | 88,447.23 |

The morning-only variant is the only one below the current best. It changes 5 of 20 days and never loses: day 2 −247, day 9 −550, day 12 −12, day 17 −240, day 18 −6. That falls short of the 16-day requirement. On the held-out days it improves by only 0.29% against the 2% bar. Its 1,055-point gain is about 2.4% of the roughly 44,449 points that are still improvable.

X has little effect. The X = 60 and X = 120 logs are identical. On day 3, only 3 of 63 cluster routes had any parcel that would have fit by capacity but was outside the tolerance. The 125-minute cap and capacity cut the route off long before X does.

## Late minutes by parcel arrival hour (20 days)

| Variant | 08:00 | 09:00 | 10:00 | 11:00 | 12:00 | 08:00–09:59 |
|---|---:|---:|---:|---:|---:|---:|
| `deadline_trip_limit` | 10,648 | 7,383 | 18 | 3,687 | 2,105 | 18,031 |
| `cluster_seed_x60` | 10,776 | 8,218 | 22 | 3,612 | 2,161 | 18,994 |
| `cluster_route_x60` | 10,338 | 7,383 | 22 | 3,603 | 2,018 | 17,721 |
| `cluster_morning_route_x60` | 10,338 | 7,383 | 18 | 3,687 | 2,105 | 17,721 |

(No late minutes for parcels arriving from 13:00 onwards.)

## Why it did not help

Clustering by distance from the seed made the morning backlog worse: 08:00–09:59 late minutes rose from 18,031 to 18,994, and 32 more parcels went undelivered. A tight cluster around one urgent seed often leaves other near-deadline parcels for a later van. Under a 125-minute trip cap, those parcels then miss their windows. Measuring distance to the nearest stop in the route builds chains that do cut the 08:00-hour backlog (10,648 → 10,338 late minutes). In the afternoon, though, they nearly double early minutes (448 → 863), because they pull in parcels whose windows have not opened. That is why restricting clustering to before 10:00 is the only version that comes out ahead. Even then, only the 08:00 hour moves (−310 late minutes). The 09:00 hour, at 7,383 late minutes, is unchanged in every route variant. This supports the earlier diagnosis that the morning rush is limited by fleet size, not by how parcels are grouped within a trip: route grouping can reshuffle at most a few hundred minutes.

## Runtime and complexity

Measured with `python3 benchmark_cluster.py` (same method as `benchmark_policies.py`: 3 repetitions × 20 days, medians; Apple Silicon, Python 3.9.6). Output: `results/cluster_benchmark.json`.

| Policy | Dispatch calls | Policy time (s) | Mean per call (ms) | p95 (ms) | Max (ms) |
|---|---:|---:|---:|---:|---:|
| `deadline_trip_limit` | 2,257 | 2.88 | 1.28 | 6.35 | 33.1 |
| `cluster_seed_x60` | 2,233 | 2.39 | 1.07 | 5.54 | 27.2 |
| `cluster_route_x60` | 2,312 | 3.05 | 1.32 | 5.93 | 26.4 |
| `cluster_morning_route_x60` | 2,247 | 2.81 | 1.25 | 6.15 | 33.5 |

Notation follows `docs/complexity_analysis.md`: n records, m eligible, k selected. In addition, p ≤ m is the tolerance pool size, and L(k,R) is the 2-opt bound defined there.

- **`cluster_seed`**: filtering is O(n), the deadline sort O(m log(m+1)), and the pool sort O(p log(p+1)). There are at most k+1 rounds. Each round scans the pool and does an O(k) cheapest-insertion check per candidate, so the total is O(n + m log(m+1) + (k+1)·p·k) + O(k) for the wait rule + L(k,R).
- **`cluster_route`**: after each accepted parcel it also refreshes the nearest-stop distances, O(p), and re-sorts the pool, O(p log(p+1)). Total: O(n + m log(m+1) + (k+1)·p·(k + log(p+1))) + L(k,R).
- **Extra space**: O(m + k), for the sorted waiting list, the pool, its distance map, and the route and stop lists.
- **Grouping by location**: let s be the number of distinct locations in the route. The supplied data has 36 delivery locations, so s ≤ min(k, 36). Insertion cost then depends on s rather than k, giving O((k+1)·p·s). The `route` refresh becomes O(p) per new location instead of per parcel.

Construction is no slower in practice than repeated-sort deadline-first. Observed routes average 18.6 stops (maximum 41), and 2-opt dominates the running time for all four policies.
