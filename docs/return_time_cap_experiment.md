# Follow-up: limiting 2-opt route extensions

> Historical investigation using `deadline_two_opt` as the reference. The current
> recommendation is `deadline_window_departure`; see [follow-up results](followup_search_results.md).

Experiment date: 1 November 2026. Reference: `deadline_two_opt` at branch
`hybrid-policy`, commit `8c77d42`. This experiment is isolated on branch
`codex/return-time-caps`; no changes to the reference policy were made.

## Motivation and diagnosis

A replay of the reference policy matched its saved logs on all 20 days.
At each dispatch, compare its initial deadline-first route with the 2-opt
route under that same snapshot, not with a separate deadline-first day's
schedule. Of 635 trips, 120 were lengthened, 16 shortened and 499 had unchanged
distance. Among lengthened trips, the median extension was 37.72 minutes and
the largest was 131.83 minutes. Net additional distance was 4,804.76 km.
Lengthened trips accounted for 93.52% of the observed within-trip timing savings.

For example, day 16 vehicle 5 planned at 11:30 and departed at 12:00 carrying
28 parcels with window 14:03–15:00. Its initial route was 57.26 km and returned
at approximately 12:57; 2-opt produced 189.09 km and returned at 15:09. Early
minutes decreased from 2,681.65 to 551.02. The route revisited some destinations
several times. This is feasible and beneficial under the stated timing metric,
which does not directly charge for driving distance; it is not necessarily
operationally efficient in a model with energy or labour costs.

On 111 trips, the extension postponed the next possible planning tick before
the end of planning. That observation alone does not establish the size of any
later delivery loss, motivating a controlled intervention.

## Fixed experimental rule

Keep deadline-first selection, the best-improvement segment-reversal operator,
and the final metric unchanged. Impose an additional latest-return limit equal
to the initial route's return time plus 0, 15 or 30 minutes, never beyond the
original 18:00 cutoff. The cap stays anchored to the initial route throughout
all improvement rounds; it is not reset after each reversal. Shorter routes
remain allowed. No waiting at customer stops is introduced.

The implementation passes a copied context with a tighter return cutoff to
Chloe's existing `two_opt` helper. Parcel selection uses the original context.
Each variant has its own policy module and results directory.

Use the existing adoption rule: at least 2% lower total penalty on days 11–20,
and no higher total penalty on days 1–10. These are development splits, not
untouched test data. The three caps and decision rule were fixed before runs.

## Results on all 20 days

| Variant | Delivered | Early minutes | Late minutes | Total penalty | Change vs reference |
|---|---:|---:|---:|---:|---:|
| Reference, unrestricted | 15,177 | 12,258.57 | 77,608.36 | 255,466.93 | — |
| Cap 0 minutes | 15,207 | 78,500.02 | 71,315.66 | 308,215.69 | +20.65% |
| Cap 15 minutes | 15,208 | 55,786.89 | 70,823.63 | 284,770.55 | +11.47% |
| Cap 30 minutes | 15,208 | 40,575.99 | 72,929.55 | 271,665.53 | +6.34% |

| Variant | Days 1–10 penalty | Change | Days 11–20 penalty | Change | Lower on how many days? |
|---|---:|---:|---:|---:|---:|
| Reference | 119,444.44 | — | 136,022.49 | — | — |
| Cap 0 | 146,517.53 | +22.67% | 161,698.16 | +18.88% | 0/20 |
| Cap 15 | 133,641.74 | +11.89% | 151,128.81 | +11.11% | 1/20 |
| Cap 30 | 126,807.54 | +6.16% | 144,857.99 | +6.50% | 4/20 |

All variants fail the adoption rule. At this experiment stage, `deadline_two_opt` remained the recommendation
under the agreed metric and decision rule. The intervention increased
completed deliveries and reduced late minutes, but the added early minutes
outweighed these gains. Therefore route extensions have costs, but banning or
limiting them at the tested levels does not improve the selected objective.
This does not establish that every extension is beneficial, that all possible
caps are inferior, or that the recommendation is globally optimal.

## Reproduction and validation

From this branch's repository root:

```bash
python3 run_all.py solution.policies.deadline_cap0 deadline_cap0
python3 run_all.py solution.policies.deadline_cap15 deadline_cap15
python3 run_all.py solution.policies.deadline_cap30 deadline_cap30
python3 check_trips.py deadline_cap0 deadline_cap15 deadline_cap30
python3 compare_days.py deadline_cap30 deadline_two_opt
```

Raw daily logs and metrics are in `results/deadline_cap{0,15,30}/day_XXX/`.
Aggregate comparisons are in `results/return_cap_summary.json`.

Validation checked the cap relative to the original route at every dispatch,
parcel preservation and input immutability, the original hard constraints,
delivery timestamp consistency, and parcel availability at planning. All 60
metric reports match recalculation from their logs. The 1,974 trips checked
had no violations. Synthetic checks also covered directed distances and
equivalence to unrestricted 2-opt when the cap cannot bind.

Further report work should distinguish metric-optimal timing from minimum
driving distance and state the lack of a held-out dataset. Keep an accurate
record of the actual assistance used for this additional experiment.
