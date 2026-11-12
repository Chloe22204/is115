> The current report and benchmark are `../report.pdf` and `../experiments/runtime/benchmark_results.json`.

# Complexity of the implemented policies

These are upper bounds for the current Python implementations, rather than
bounds for an idealised version of each heuristic. This document is supporting
analysis for the report.

## Notation and assumptions

For one dispatch call, `n` is the number of supplied parcel records, `m` is the
number eligible for selection, and `k` is the number selected. Thus
`0 <= k <= m <= n`. Already assigned or delivered records still count in `n`.
Each call uses a fixed snapshot; future arrivals are not included. The
simulator passes every parcel that has arrived so far, so `n` grows during the
day up to the day's total (763-811 on the supplied days).

`k` is not capped at 30. Capacity is 30 size units and parcel sizes range from
0.2 to 1.8 (median 0.9), so up to 150 of the smallest parcels could fit. Route
lengths observed in the saved logs: `deadline_trip_limit` mean 18.6, max 41;
`deadline_window_departure` mean 23.8, max 43; `baseline` mean 15.5, max 37.
The `nearby_two_opt` and `deadline_two_opt` logs (commit `3812151`) reach
46 and 43. R was not measured.

`V = 10` vehicles and `T = 58` planning ticks (08:00 to 17:30 every ten
minutes). The simulator calls dispatch once per idle vehicle per tick.

Dictionary/set operations take average O(1), IDs have bounded length, and
numeric operations and distance lookups take O(1). Python list copying,
slicing and removal take linear time. Sorting uses O(s log(s+1)) time and
O(s) auxiliary space for s items. Space below excludes the supplied snapshot
and distance table, but includes returned routes and temporary containers.

Use the following shorthand for bounds, not measured running times:

- **G(n,m,k) = n + 1 + (k+1)m log(m+1)**: repeated-sort greedy construction.
- **L(k,R) = 1 + k + R k³**: one local search, where R counts complete
  neighbourhood scans, including the final unsuccessful scan.

R depends on the input. Strict improvements over a finite set of permutations
ensure termination, but do not prove a polynomial bound on R. Consequently,
calling the entire local search simply “O(k³)” would omit a necessary factor.

## Construction and standard local search

| Implementation / family | Time per dispatch | Extra space |
|---|---|---|
| `baseline` | O(n + 1 + m log(m+1)) | O(m+1) |
| `deadline_first`, `nearby_first`, `window_aware`, `deadline_size_ties` | O(G(n,m,k)) | O(m+1) |
| Urgency/nearby hybrids without local search (`hybrid_u*`) | O(G(n,m,k)) | O(m+1) |
| `nearby_local_search` (pair swaps) | O(G(n,m,k) + L(k,R)) | O(m+k+1) |
| `nearby_two_opt`, `deadline_two_opt`, urgency hybrids with 2-opt | O(G(n,m,k) + L(k,R)) | O(m+k+1) |

These policies and their results are included in this submission. The
2-opt bound applies to `helpers.two_opt`, which `deadline_window_departure`
and `deadline_trip_limit` call when they dispatch.

Filtering scans all n records. Baseline sorts once, then scans candidates once.
The other constructors sort remaining candidates after each accepted parcel,
with up to one final failed round. Sorting keys use a fixed number of lookups
and arithmetic operations. Candidate scanning and list removal cost O(m) per
round, within G. If k grows to m, G becomes O(n + 1 + m² log(m+1)).

A pair-swap or 2-opt scan tries O(k²) moves. Each candidate copies O(k) IDs and
recalculates arrival times, early/late penalties, distance and return feasibility
in O(k). Thus one scan costs O(k³); the initial evaluation costs O(k).
Only the current, candidate and best routes are retained, giving linear space.
`helpers.route_timing_penalty` itself takes O(k+1) time and space because it
builds leg and penalty lists. Reordering preserves the initially checked load.

The lecture's O(k²) scan for distance-only symmetric TSP can evaluate a reversal
using a constant-time boundary-edge delta. Our timing objective recalculates
subsequent delivery times, so that bound does not describe this implementation.

## Candidate selection and departure rules

| Implementation / family | Time per dispatch | Extra space |
|---|---|---|
| `candidate_selection` (`cand_*` wrappers), q builders | O(Σ[j=1..q] (G(n,m,k_j) + L(k_j,R_j))) | O(m+K+q+1), K = max k_j |
| `holdback_two_opt` (`holdback_h*`) | O(n+1 + G(n',m',k) + L(k,R)) | O(n+k+1) |
| `wait_to_fill` (`wait_f*`) | O(G(n,m,k) + L(k,R) + k) | O(m+k+1) |
| `deadline_return_cap` (`deadline_cap*`) | O(G(n,m,k) + k + L(k,R)) | O(m+k+1) |
| `deadline_window_departure`: defer / empty route | O(G(n,m,k) + k) | O(m+k+1) |
| `deadline_window_departure`: dispatch route | O(G(n,m,k) + k + L(k,R)) | O(m+k+1) |
| `deadline_trip_limit` (selected) | Same as `deadline_window_departure`, plus O(1) | O(m+k+1) |

`deadline_trip_limit` makes one shallow copy of the fixed-schema context to
lower `return_cutoff`, then calls `deadline_window_departure`. That costs O(1),
so its bounds are the same. A shorter limit can make k smaller per trip, and
vans become idle more often, which increases the number of calls.

Apart from the two `deadline_window_departure` rows and `deadline_trip_limit`,
the policies in this section were removed in commit `92dee2d`.

Candidate selection constructs and improves q routes sequentially. Scoring each
route costs O(k_j+1), already included above. It keeps the best route and the
current candidate, rather than q complete routes. The builders occupy O(q)
persistent space and take O(q) time to initialise, once per factory call.
The tested pool sizes two and five are constants, but q makes the scaling clear.

Holdback scans n records and creates a new **shallow dictionary of all visible
records**, including assigned/delivered ones. Its size n' can be O(n), even when
few parcels are waiting. Records and the distance table are not deep copied.
The reduced eligible count m' is at most m. This is why its extra space differs
from the other policies.

Wait-to-fill builds and improves a route before deciding whether to return it
or wait. Returning an empty list therefore does not make that call cheap.
Return caps add a linear distance calculation and a fixed-schema shallow
context copy before 2-opt. Window-aligned departure checks the greedy route in
O(k); a deferral skips 2-opt in that call, but triggers fresh planning later.

## Additional improvement experiments

For these bounds, k₀ is the initial route length, K the largest route length
reached, B the number of accepted insertions/exchanges, and R_total the total
number of 2-opt scans across the initial search and every subsequent restart.
All refer to one dispatch call. Set
`G₀ = G(n,m,k₀)` and `L_total = B+1 + (B+1)K + R_total K³`.
This L_total safely includes all initial route evaluations and search restarts.

| Implementation | Time per dispatch | Extra space |
|---|---|---|
| `deadline_backfill` | O(G₀ + (B+1)[1 + m(K+1)²] + L_total) | O(m+K+1) |
| `deadline_exchange` | O(G₀ + (B+1)[n+1 + m log(m+1) + K log(K+1) + r w²(K+1)] + L_total) | O(m+K+r+w+1) |
| `deadline_relocate` | O(G₀ + 1 + (A+1)(k+1) + (A+R_total)k³) | O(m+k+1) |

Backfill tries up to m waiting parcels at up to K+1 positions. Each candidate
copy, timing evaluation and distance calculation costs O(K+1), giving
O(m(K+1)²) per insertion scan. A successful scan adds one parcel and reruns
2-opt. There are at most B+1 scans; B <= m-k₀. The initial waiting-list filter
and sort are covered by G₀. The bound allows scans that terminate early.

Exchange sorts **all** remaining candidates before retaining w <= 8, and sorts
the selected route before retaining r <= 4 removal options. It tries O(r w²)
one-for-two replacements, with two orders per pair and O(K+1) work per trial.
The constants four and eight bound the trial set, not the preceding full-list
sort. Every accepted exchange increases the route count by one, so
B <= m-k₀, even though a removed parcel can be reconsidered later.

Relocation retains the same k parcels. A is the number of relocation scans,
including the final failed scan. Each scan tries O(k²) source/position pairs
and evaluates them in O(k), for O(k³). Each successful scan restarts 2-opt,
at most A+1 total invocations including the initial search. Strict penalty
decrease and finitely many orders ensure termination; neither A nor R_total
has a demonstrated polynomial bound. The extra linear terms cover initial
evaluations and small/empty routes.

## Whole-day cost and the recommended policy

If a day invokes dispatch Q times, total policy time is the **sum of the
per-call bounds**. Because each tick calls dispatch at most once per idle
vehicle, Q <= V·T = 580 per day. Benchmarks recorded 614 to 1,902 calls over
all 20 days (about 31 to 95 per day), so the bound is loose. Sum with the actual n_i, m_i, k_i and R_i for
each call. Q includes
calls that return no route. It is not the number of trips or deliveries.
Waiting changes vehicle availability and can increase Q, so equal asymptotic
per-call bounds do not imply equal daily runtime.

For `deadline_window_departure`, sum G(n_i,m_i,k_i)+k_i across all calls and add
L(k_i,R_i) only for calls that reach 2-opt. A simple uniform upper bound is
O(Q[n_max+1 + (k_max+1)m_max log(m_max+1) + k_max + R_max k_max³]).
Peak policy space remains O(m_max+k_max+1), rather than the sum over calls.
The current simulator has a fixed fleet and planning schedule; the expression
also explains how cost would scale if these were expanded.

These bounds exclude simulator input loading, snapshot copying, event handling
and logging. Report measured dispatch time and total simulator time separately;
measurements describe the tested workload, while the bounds describe scaling.

## Supporting tools

`performance_monitor.calculate_metrics`: with N input parcels, E events and P
distinct trips, time is O(N+E+1+P log(P+1)) and extra space O(N+P+1). It builds
parcel/trip lookups, scans events, sorts trip summaries and scans parcels. Its
distance-list argument is unused by the calculation. CLI input loading adds
O(N+D+E) time and storage for D distance rows and the parsed inputs/log.

The exact-search component of `diagnose_small_cases.py` enumerates ordered
subsets of p waiting parcels.
There are S(p) = Σ[i=0..p] p!/(p-i)! such subsets. Full route evaluation and
list operations give O((p+1)S(p)) time, which is factorial, and O(p²+1)
auxiliary recursion space because each recursion level retains list copies.
This bound excludes collecting cases through simulator runs and writing output.
The separate fixed-selection permutation check is also factorial. This tool
uses bounded cases (up to eight parcels); it is diagnostic evidence, not a
scalable dispatcher or proof of full-day optimality.

## Data structures and what the bounds do not claim

Lists represent delivery order and support sorting, slicing and reversals.
Dictionaries provide parcel and directed-distance lookups. The current
policies use no sets; the simulator uses sets to track parcel states. Their average constant-time lookups explain
the assumptions above. The local searches evaluate feasible neighbours and
strictly reduce a trip-level timing objective; they do not prove a globally
optimal trip, packing, fleet schedule or daily score.

Source basis: the policy modules in `solution/policies/`, shared `helpers.py`,
`solution/performance_monitor.py`, and `diagnose_small_cases.py`. Cite the
project brief and the relevant course material separately in the final report.
