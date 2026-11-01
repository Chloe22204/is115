# Bounded exhaustive-search diagnosis

Date: 1 November 2026. Recommended policy inspected: `deadline_two_opt` from
Chloe's branch, commit `8c77d42`. No production policy was changed for this
diagnosis. Run `python3 -B diagnose_small_cases.py` from the repository root to
reproduce `results/small_case_diagnosis.json`.

## Scope and objective

The diagnostic replays days 1, 7 and 16 under the recommended policy. Replay
logs match the saved reference logs exactly. It captures the first non-empty
dispatch snapshot at or after 08:00, 10:30, 12:00 and 15:00 on each day.

Each problem has at most eight parcels. When the waiting set is larger, a
deterministic, location-diverse sample combines urgency and proximity; it is
not a random or representative sample. In addition, a fixed-prefix suffix
problem is derived from each day's noon construction when enough parcels can
be fixed to leave less than five capacity units. The prefix is from the initial
deadline-first construction, not the final 2-opt order or an observed completed
prefix. Its deliveries and their penalty are fixed and omitted as a constant
from the suffix comparison. The suffix starts at the prefix endpoint and must
still return to the real hub, using the remaining time, range and capacity.

The single-trip surrogate objective is:

`early minutes + late minutes + 240 * candidate parcels omitted from this trip`.

This charges omitted candidates as though they were ultimately undelivered.
In a full day, another van or later trip might serve them. Therefore the exact
solution is exact only for this defined bounded subproblem, not a complete
dispatch snapshot with additional parcels, nor the whole day's actual score.

Three cases use the complete waiting set (eight parcels at opening); the
other 12 are reduced subproblems. All candidates had arrived at the source
planning time. The eight-parcel unconstrained cases do not stress capacity
because parcel sizes are small; the suffix cases deliberately cover that gap.

## Enumeration and independent checks

For eight parcels, enumerate every ordered subset, including the empty route:
`sum(8! / (8-k)!, k=0..8) = 109,601` candidates. Across 15 cases this is
1,644,015 candidates. There is no feasibility pruning, so potentially feasible
orders cannot be lost by a pruning assumption. Evaluate capacity, round-trip
range, return time and every delivery's window deviation independently of the
policy helper. A separate enumeration of permutations of the heuristic's exact
selected set distinguishes order defects from selection defects.

The enumerator matched an independent combinations-of-permutations calculation
on 20 tiny generated cases, including directed distances. All reported
heuristic routes were checked to be reversal local optima. Inputs remain
unchanged. Exact feasibility and best score were checked for each reported
optimal route, and fixed-prefix capacity was verified against the source data.

## Results

| Day | Snapshot / type | Heuristic score | Exact score | Gap |
|---|---|---:|---:|---:|
| 1 | Opening, complete set | 0.000 | 0.000 | 0.000 |
| 1 | Morning, reduced set | 88.833 | 88.833 | 0.000 |
| 1 | Noon, reduced set | 81.660 | 68.628 | 13.032 |
| 1 | Noon, reduced fixed-prefix suffix | 770.012 | 540.044 | 229.968 |
| 1 | Afternoon, reduced set | 0.000 | 0.000 | 0.000 |
| 7 | Opening, complete set | 0.000 | 0.000 | 0.000 |
| 7 | Morning, reduced set | 172.671 | 168.009 | 4.662 |
| 7 | Noon, reduced set | 69.839 | 69.839 | 0.000 |
| 7 | Noon, reduced fixed-prefix suffix | 778.401 | 778.401 | 0.000 |
| 7 | Afternoon, reduced set | 480.000 | 240.000 | 240.000 |
| 16 | Opening, complete set | 0.000 | 0.000 | 0.000 |
| 16 | Morning, reduced set | 367.561 | 367.561 | 0.000 |
| 16 | Noon, reduced set | 14.196 | 14.196 | 0.000 |
| 16 | Noon, reduced fixed-prefix suffix | 1,200.000 | 480.000 | 720.000 |
| 16 | Afternoon, reduced set | 480.000 | 480.000 | 0.000 |

The heuristic matches the best score in 10 cases and misses it in five. Three
cases have an ordering gap and three have a selection gap; one has both. These
counts are descriptive of the selected cases, not an estimate of failure rate
on full dispatches or unseen data. All five counterexamples are reduced cases.

### Ordering limitation

In day 1's reduced noon case, both routes carry the same eight parcels.
The heuristic scores 81.660 and returns at about 16:40. Exhaustive search finds
a route scoring 68.628 and returning at about 16:03. No single improving segment
reversal exists from the heuristic route, confirming a local optimum rather
than global optimality. The exact route has more late minutes but sufficiently
fewer early minutes to improve their sum.

### Selection limitation

In day 16's derived fixed-prefix case, the remaining capacity is 3.4 units.
The heuristic chooses three parcels totalling 3.4 units, all within their
windows, and leaves five candidates out: score 1,200. The exact solution
chooses six parcels totalling 3.2 units, all within their windows, leaving two
out: score 480. Deadline-first prioritises urgency, not the most parcels per
capacity unit; 2-opt cannot replace that selected set. The six-parcel route
also returns about 20 minutes earlier in this subproblem.

In day 7's reduced afternoon case, the heuristic chooses six candidates, all
on time. An exact route carries those six plus another candidate, also on
time, while satisfying range and the 18:00 return deadline. The optimiser only
reorders a fixed set and requires a strict timing improvement, so zero timing
penalty does not trigger attempts to add omitted candidates or improve tied
routes for later use.

## Interpretation and possible follow-up

This establishes concrete limits of the route neighbourhood and parcel
selection under the defined small-case objective. It does not prove that a
particular replacement improves the full-day metric. Serving a different
parcel now can affect which parcels another vehicle serves later.

A targeted next hypothesis is insertion/backfill or an exchange between a
selected parcel and waiting parcels, with full route feasibility checks. Any
new policy should be evaluated over the unchanged 20 days and original metric,
using the existing adoption rule. Do not infer a full-day improvement directly
from the bounded-case gap or call these days a held-out test set.

The factorial search is a diagnostic tool, not a proposed dispatcher for
hundreds of waiting parcels. Record the actual assistance used for this
diagnosis alongside the other experiments.
