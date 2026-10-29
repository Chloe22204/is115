# Experiment notes for team discussion

These notes organise the current evidence. They are not the final report.

## Objective and assumptions

Minimise `240 * undelivered + early_minutes + late_minutes`. Timing deviations
are summed across delivered parcels, with zero penalty inside the preferred
window, including its endpoints. The fixed undelivered penalty replaces timing
penalties for those parcels. The chosen weight is a team preference, not an
estimated monetary cost; there is no premium-service or revenue field in the
supplied data. Early and late minutes currently have equal weight.

The objective permits a very late delivery to incur more penalty than leaving
that parcel undelivered. This is an intentional consequence of allowing severe
timing failures to outweigh some completed deliveries, and should be stated in
the report. None of the current policies explicitly chooses to drop a parcel
based on that comparison.

All policies use identical inputs and hard constraints. There is no waiting
at delivery stops. Departure is 30 minutes after planning; speed is 1 km per
minute. Every range check includes the return leg. Distances are accessed by
direction even though the supplied matrix is symmetric.

## What the experiments show

- Baseline: 6,421 deliveries out of 15,867, or 40.47%. Its 200 first trips
  average 26.03% capacity utilisation and 285.51 km. There are 413 trips across
  the 20 days. Long trips and light loads occur together; capacity alone does
  not explain the low delivery rate.
- Deadline-first: dramatically improves both deliveries and lateness. Its
  distance tie-breaker matters, so the improvement cannot be attributed to
  deadline priority alone.
- Nearby-first: delivers 26 more parcels than deadline-first and scores 0.61%
  better at weight 240. It has more late minutes but fewer early minutes.
- Window-aware: reduces early minutes but produces very high lateness. Because
  the lowest candidate score wins, adding a parcel's already accumulated
  lateness to that score can repeatedly deprioritise it. On day 1, P000794 has
  an 11:36 deadline and is delivered around 11:48 by nearby-first but 15:38 by
  window-aware. A replay confirmed it remained feasible at several intervening
  planning decisions.
- Pair swaps: improve the full-day score by 7.04% against nearby-first, although
  they deliver 57 fewer parcels. Early-minute reductions outweigh additional
  lateness and undelivered penalties at the chosen weight.
- 2-opt: achieves the lowest total penalty, 319,101.86, with 15,174 deliveries.
  It improves on baseline by 88.19%, nearby-first by 9.72%, and pair swaps by
  2.89%. It wins against pair swaps on 19 of 20 days, not all days.

## Why local route improvement need not improve every day

Each local-search call fixes the selected parcels and improves the current
trip's timing penalty. It does not optimise the complete day's schedule.
Reordering can change return time, which changes future vehicle availability,
parcel assignments and subsequent routes. Therefore lower per-trip timing
penalty does not guarantee more deliveries or lower full-day penalty.

## Connection to Week 11

Course sources: `11 Heuristics Part 2a - Greedy Algo.pdf` and
`11 Heuristics Part 3 - Local Search.pdf` from Week 11.

Nearby-first adapts nearest-neighbour greedy construction to parcel capacity,
vehicle range and a return deadline. Pair swaps and 2-opt begin with a complete
feasible trip, examine a neighbourhood, apply the best strict improvement,
and stop at a local optimum.

Pair swaps exchange two parcel positions. The 2-opt variant reverses a
contiguous segment, reconnecting its boundary edges. Full reversal is included:
even when total distance is unchanged, delivery times and penalties can change.
The code recalculates the complete route, so it also handles directed distances.

The lecture illustrates distance minimisation. Our adapted objective is
early/late timing penalty, with distance and return time enforced as hard
constraints. Do not claim the implementation uses constant-time move scoring.

## Complexity of the actual implementation

Per dispatch call, let n be all supplied parcel records, m the waiting records,
k the selected route length, and R the number of neighbourhood scans including
the final scan without an improvement. Assume average O(1) dictionary access,
bounded-length parcel IDs and constant-time numeric operations. Extra space
excludes the supplied parcel and distance dictionaries.

| Policy | Time | Extra space |
|---|---|---|
| Baseline | O(n + m log m) | O(m) |
| Deadline-first / nearby-first / window-aware | O(n + (k + 1)m log m) | O(m) |
| Nearby + pair swaps / nearby + 2-opt | O(n + (k + 1)m log m + Rk^3) | O(m + k) |

Filtering scans all n records. The baseline sorts once. The other constructors
sort the remaining candidates after each addition, with up to one final
unsuccessful scan. Candidate scanning and list removal each cost O(m), within
the stated bound. For very small m, sorting/scanning costs can be written using
`log(m + 1)` to avoid edge-case notation.

For local search, there are O(k^2) moves per scan. Each candidate is copied and
its delivery times and constraints are recalculated in O(k), giving O(k^3) per
scan. Strict improvement and finitely many permutations ensure termination,
but do not establish a polynomial bound on R. Only a few candidate routes
are held at once, so space is linear, not cubic. Include the initial O(k)
evaluation for degenerate empty/single-parcel routes if giving an exact bound.

The lecture's O(k^2) neighbourhood scan for symmetric distance-only TSP can
use O(1) distance deltas from the changed boundary edges. Timing penalties
require a different evaluation here. A day's dispatch cost sums these
per-call costs over its actual planning calls; simulator overhead is additional.

## Sensitivity to undelivered penalties

Recalculate scores from existing reports, without changing policies or logs.
The following scores are rounded to whole points for presentation.

| Policy | Weight 120 | Weight 240 | Weight 480 |
|---|---:|---:|---:|
| Deadline-first | 276,327 | 355,647 | 514,287 |
| Nearby-first | 277,273 | 353,473 | 505,873 |
| Window-aware | 450,315 | 525,915 | 677,115 |
| Pair swaps | 245,564 | 328,604 | 494,684 |
| 2-opt | 235,942 | 319,102 | 485,422 |

2-opt ranks first at all three weights. This supports robustness within the
tested range; it does not prove robustness for arbitrary weights or objectives.
Summing stored rounded early/late components can differ by a few hundredths
from summing daily penalties, which were rounded after the full calculation.

## Runtime evidence

The benchmark performs a day-1 warm-up for each policy and three measured
20-day repetitions, reversing policy order on the middle repetition. It
measures simulator construction and execution, including temporary event logs,
and separately times policy calls. Metric calculation and interpreter startup
are excluded. Policy calls differ across methods because fleet schedules differ.

| Policy | Median total seconds | Median policy seconds |
|---|---:|---:|
| Baseline | 0.94 | 0.04 |
| Deadline-first | 3.32 | 0.22 |
| Nearby-first | 3.45 | 0.22 |
| Window-aware | 3.38 | 0.35 |
| Pair swaps | 5.67 | 3.04 |
| 2-opt | 5.94 | 3.11 |

These local timings are practical for the supplied data; they are not a
scalability guarantee. Reproduce using `python3 benchmark_policies.py`.
Raw repetition records are in `results/benchmark.json`.

## Provisional recommendation and remaining work

Recommend nearby-first + 2-opt among the tested methods at the chosen metric.
Its measured objective improvement, sensitivity results and modest runtime
support the trade-off. It delivers fewer parcels than the simpler greedy
policies, has no global-optimality guarantee, and only changes within-trip order.

All 20 days informed development and evaluation. There is no untouched test set;
state this limitation rather than claiming verified generalisation. More
policies are optional, not necessary to explain the current experiments.

Before submission:

- Both teammates should review and be able to explain the policy code and score.
- Complete and verify actual prompts/responses in `ai_log.md` and references;
  existing placeholder entries are not a complete assistance record.
- Select a concise comparison table and suitable figures for the final report.
- Write the report in the team's own voice, within eight pages excluding references.
- Verify reproduction commands and the ZIP contents against the brief.

## Further hypotheses and revised recommendation

After the provisional recommendation above, four further hypotheses were
tested on the same 20 days. The recommendation is now deadline-first + 2-opt
(`deadline_two_opt`). Nearby + 2-opt and all earlier results are kept as
comparisons.

### Hypotheses and implementation

1. **Urgency selection + 2-opt** (`hybrid_urgent_nearby.py`, wrappers
   `hybrid_u*_two_opt`, and `deadline_two_opt.py`). Build one route by adding
   parcels in deadline order while load < U × capacity, then in distance order,
   then apply the same 2-opt as `nearby_two_opt`. U = 0 reproduces nearby-first
   and U = 1 reproduces deadline-first. `deadline_two_opt` is the U = 1 case,
   written directly as `deadline_first.dispatch` followed by `two_opt()` from
   `two_opt_helper.py`.
2. **Candidate selection** (`candidate_selection.py`, wrappers `cand_*`). For
   each dispatch, build one 2-opt route per U in a pool ([1, 0] or
   [1, 0.75, 0.5, 0.25, 0]) and return the lowest score. Scoring A is timing
   penalty − 240 × parcels; scoring B divides that by round-trip km.
3. **Hold-back** (`holdback_two_opt.py`, wrappers `holdback_h*`). Before
   deadline-first + 2-opt, omit waiting parcels whose window opens more than H
   minutes after a direct hub-to-parcel arrival, provided a later direct trip
   could still return by 18:00 minus a 30-minute margin.
4. **Wait-to-fill** (`wait_to_fill.py`, wrappers `wait_f*`). Build the
   deadline-first + 2-opt route but return no route (wait 10 minutes) unless
   load ≥ F × capacity, a parcel would arrive within 30 minutes of its window
   end, the van has been ready for 30 minutes, or it is 15:00 or later.

### Correctness checks

- `two_opt_helper.two_opt()` applied to nearby-first routes reproduces
  `results/nearby_two_opt` logs byte for byte (days 001-003).
- `deadline_two_opt` and `hybrid_u100_two_opt` logs are byte-identical on all
  20 days. U = 0 and U = 1 hybrids match nearby-first and deadline-first on all
  20 days.
- Candidate pools [1] and [0] reproduce `deadline_two_opt` and `nearby_two_opt`
  (days 001-003). Hold-back with H = 100000 and wait-to-fill with F = 0
  reproduce `deadline_two_opt` (days 001-003).
- `check_trips.py` re-checks every logged trip against capacity, round-trip
  range, the 18:00 return and single, post-arrival delivery of known parcels.
  It reports no violations for any of the new policies, and it detected each
  of six deliberately injected faults in a test copy of a log.
- `deadline_two_opt` day 001 was re-run from scratch and its log is
  byte-identical to the saved result.

### Results (20-day totals)

| Policy | Total penalty | Delivered | Undelivered | Early min | Late min | Trips |
|---|---:|---:|---:|---:|---:|---:|
| `nearby_two_opt` (previous recommendation) | 319,101.86 | 15,174 | 693 | 9,326.46 | 143,455.43 | 647 |
| `deadline_two_opt` (recommended) | 255,466.93 | 15,177 | 690 | 12,258.57 | 77,608.36 | 635 |
| `hybrid_u75_two_opt` | 268,031.47 | 15,156 | 711 | 12,031.51 | 85,359.97 | 641 |
| `hybrid_u50_two_opt` | 286,071.79 | 15,170 | 697 | 11,133.94 | 107,657.82 | 644 |
| `hybrid_u25_two_opt` | 296,843.07 | 15,166 | 701 | 10,180.95 | 118,422.09 | 643 |
| `cand_p2_A` | 304,815.10 | 15,186 | 681 | 9,590.86 | 131,784.21 | 645 |
| `cand_p2_B` | 292,548.30 | 15,187 | 680 | 10,768.46 | 118,579.85 | 653 |
| `cand_p5_A` | 300,687.70 | 15,180 | 687 | 9,851.62 | 125,956.13 | 643 |
| `cand_p5_B` | 288,651.61 | 15,183 | 684 | 10,322.52 | 114,169.10 | 655 |
| `holdback_h30` | 292,565.53 | 15,202 | 665 | 5,198.92 | 127,766.65 | 667 |
| `holdback_h60` | 260,252.25 | 15,179 | 688 | 10,039.66 | 85,092.58 | 642 |
| `holdback_h120` | 255,466.93 | 15,177 | 690 | 12,258.57 | 77,608.36 | 635 |
| `wait_f50` / `wait_f70` / `wait_f90` | 252,768.31 | 15,166 | 701 | 14,783.73 | 69,744.58 | 610 |

`deadline_two_opt` is 19.94% below `nearby_two_opt`. `holdback_h120` logs are
identical to `deadline_two_opt`. The three wait-to-fill variants produce
identical logs: in every call where they waited, the route load was between 9%
and 49% of capacity, so thresholds of 0.5, 0.7 and 0.9 never led to a different
decision.

### Daily comparisons against `deadline_two_opt`

From `compare_days.py`, with two-sided exact sign tests on non-tied days:

| Comparison | Days `deadline_two_opt` lower | Days other lower | Ties | Sign test p | Days 001-010 | Days 011-020 |
|---|---:|---:|---:|---:|---|---|
| vs `nearby_two_opt` | 20 | 0 | 0 | 1.9e-6 | 10-0 | 10-0 |
| vs `wait_f70` | 8 | 12 | 0 | 0.50 | 6-4 | 2-8 |
| vs `holdback_h60` | 9 | 8 | 3 | 1.00 | 3-5 (2 ties) | 6-3 (1 tie) |

Against `nearby_two_opt`, `deadline_two_opt` is lower on every day, with daily
differences from 452 to 5,611 points; it has fewer late minutes on all 20 days
and more early minutes on 16. Wait-to-fill has the lowest 20-day total but is
lower on only 12 of 20 days, has a higher total on days 001-010 (mean daily
difference +858.50) and a lower total on days 011-020 (−1,128.36); it was
rejected under the pre-set rule. Hold-back H = 60 is split almost evenly.

### Runtime

Measured with a copy of `benchmark_policies.py` (3 repetitions of all 20 days),
always paired with `deadline_two_opt` in the same session because machine load
varied between sessions by about a factor of two:

| Session | `deadline_two_opt` median total s | Other policy median total s |
|---|---:|---:|
| with `cand_p5_A` | 14.80 | 48.59 |
| with `holdback_h60` | 7.28 | 7.55 |
| with `wait_f70` | 7.32 | 7.63 |

`results/benchmark.json` was not regenerated, so its figures do not include
`deadline_two_opt`.

### Limitations

- All 20 days were used for development and evaluation; there is no untouched
  test set.
- About eleven variants were tried and the best was kept, so the selected
  policy's advantage may be mildly overstated by this selection effect.
- The split into days 001-010 and 011-020 is a robustness check only. Days
  011-020 were not strictly held out, because they informed the same
  development.
- Comparisons are on the chosen metric at weight 240 with equal early and late
  weights; the new policies have not been re-checked at weights 120 and 480.
