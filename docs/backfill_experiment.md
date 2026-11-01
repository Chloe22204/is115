# Follow-up: insertion/backfill after deadline-first + 2-opt

> Historical investigation using `deadline_two_opt` as the reference. The current
> recommendation is `deadline_window_departure`; see [follow-up results](followup_search_results.md).

Date: 1 November 2026. Reference policy: Chloe's `deadline_two_opt`, commit
`8c77d42`. This experiment is on branch `codex/return-time-caps`. The
reference policy and its saved results were not changed.

## Hypothesis and fixed rule

The bounded exhaustive-search diagnosis found selection gaps and a reduced
case in which an additional parcel could be carried by a different route.
The hypothesis is that explicitly trying to insert waiting parcels after
2-opt may exploit spare space and route feasibility that greedy construction
did not use.

Start with the exact `deadline_two_opt` route. Preserve every selected parcel.
For each waiting, unassigned, undelivered parcel that fits the remaining
capacity, try every insertion position and evaluate the complete route. Reject
range or return-cutoff violations. An insertion must strictly decrease:

`trip timing penalty - 240 * number of selected parcels`.

Equivalently, the added timing penalty must be less than 240. Choose the best
change; ties use complete route distance, candidate deadline, parcel ID, then
insertion position. Apply that insertion and rerun the unchanged 2-opt helper.
Repeat until no improving feasible insertion exists. This is a trip-level
proxy: parcels omitted now may still be served later in the real simulation.

This version does not remove or replace selected parcels, use future arrivals,
or repair an infeasible insertion by rearranging existing stops first. In
particular, it does not recover the previously identified day-7 reduced
seven-parcel example: that example needs a different order before the insertion
is feasible. This limitation was confirmed before the full experiment.

Use the unchanged final metric, 240 per undelivered parcel plus early and late
minutes. Adoption requires at least 2% lower penalty on days 11–20 and no
worsening on days 1–10. The split is a development comparison, not held-out data.

## Results

| Measure | Reference | Backfill |
|---|---:|---:|
| Delivered | 15,177 | 15,178 |
| Undelivered | 690 | 689 |
| Trips | 635 | 635 |
| Early minutes | 12,258.57 | 12,258.57 |
| Late minutes | 77,608.36 | 77,622.31 |
| Total penalty | 255,466.93 | 255,240.88 |
| Days 1–10 penalty | 119,444.44 | 119,444.44 |
| Days 11–20 penalty | 136,022.49 | 135,796.44 |

Backfill saves 226.05 points overall (0.0885%). It improves one daily score,
worsens one, and leaves 18 unchanged. Day 11 gains one delivery and saves 240
points; day 17 adds 13.95 late minutes. The second-half improvement is 0.1662%, below
the pre-existing 2% adoption threshold, so it is not adopted under that rule.

At this experiment stage, `deadline_two_opt` remained the recommendation
under the stated adoption criterion. Do not claim backfill has a worse aggregate score: its improvement
is real but small on this dataset. Nor does this establish that selection
changes cannot help. Parcel replacement and reordering to enable insertion
remain outside this neighbourhood, and all days have informed development.

## Reproduction and validation

```bash
python3 run_all.py solution.policies.deadline_backfill deadline_backfill
python3 check_trips.py deadline_backfill
python3 compare_days.py deadline_backfill deadline_two_opt
```

Daily logs and metrics are in `results/deadline_backfill/day_XXX/` and aggregate
figures in `results/backfill_summary.json`.

Checks on all 15 bounded cases verify feasibility, preservation of the initial
selected set, unique parcel IDs, unchanged snapshots, no worsening of the
trip proxy, and no remaining improving immediate insertion at termination.
A small directed-distance synthetic example confirms the implementation can
insert a parcel skipped by construction after 2-opt changes route feasibility.
Eligibility and empty-input checks also passed. All 20 full-day reports match
recalculation, and 635 trips passed hard-constraint, delivery-time and parcel
availability checks.

Additional computation depends on the number of insertions. With m waiting
parcels and k stops, one scan considers up to O(mk) insertion positions and
evaluates each full route in O(k), or O(mk²). Each accepted insertion also
reruns 2-opt. This is additional work beyond the reference policy; no separate
runtime benchmark was performed for this follow-up.

Record the actual assistance used for this experiment in the project references.
