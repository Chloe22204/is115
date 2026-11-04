# Follow-up: limiting trip length

Reference: `deadline_window_departure` (branch `codex/return-time-caps`, commit `3812151`).
Selected policy: `deadline_trip_limit` (`solution/policies/deadline_trip_limit.py`).

## Diagnosis

- 561 of the reference's 687 undelivered parcels arrive too late for any van to
  return by 18:00 (`analyze_floor.py`). No policy can recover them, so 134,640
  points is a lower bound on the penalty.
- All 76,184 late minutes are avoidable in isolation. 62k come from two daily
  groups: arrivals 08:xx due 10:xx, and arrivals 09:xx due 10:00-11:00.
- By about 09:30 all 10 vans have left on ~3-hour trips; the first returns
  around 10:20, so these parcels go out on second trips at 11:00-12:00.

## Rule

Every trip must return within 125 minutes of leaving the hub. Otherwise
identical to `deadline_window_departure`.

## Results (20 days)

| Policy | Penalty | Undelivered | Early min | Late min |
|---|---:|---:|---:|---:|
| deadline_window_departure | 242,935.56 | 687 | 1,871.91 | 76,183.63 |
| deadline_trip_limit | 179,088.70 | 645 | 447.91 | 23,840.78 |

Days 1-10: 90,383.74 (-21.1%); days 11-20: 88,704.96 (-30.9%). No worse than
the reference on any day; best single-day saving 7,750.

## Choosing the limit (split-half check)

> **Not reproducible from saved results:** only the 125-minute run is saved in
> `results/`; the other limits' logs are not in the repository. The 125 row
> matches `results/deadline_trip_limit`. Both halves informed the final choice
> of 125, so neither half is an untouched test set.

| Limit (min) | Days 1-10 | Days 11-20 | All 20 |
|---:|---:|---:|---:|
| 100 | 307,499 | 306,763 | 614,262 |
| 105 | 95,276 | 94,636 | 189,912 |
| 110 | 92,071 | 90,907 | 182,979 |
| 115 | 93,765 | 92,966 | 186,731 |
| 120 | 93,124 | 92,242 | 185,366 |
| 125 | 90,384 | 88,705 | 179,089 |
| 130 | 89,305 | 91,286 | 180,590 |
| 135 | 100,575 | 105,314 | 205,889 |
| 140 | 108,854 | 113,803 | 222,657 |

Choosing on days 1-10 picks 130, which scores 28.9% below the reference on days
11-20. Choosing on days 11-20 picks 125, which scores 21.1% below it on days 1-10.
Limits of 100 or less, or 135 or more, score much worse.

## Robustness (modified copies of the data)

> **Not reproducible from saved results:** the modified data copies, their
> logs and the script that produced them are not in the repository.

Gap to the best of four candidates in each scenario (lower is better):

| Scenario | window_departure | 10:00 morning cap | trip <= 120 | trip <= 125 |
|---|---:|---:|---:|---:|
| Supplied data | +36% | +12% | +4% | best |
| 7 vans | +56% | +15% | best | +4% |
| 8 vans | +56% | +2% | best | +6% |
| 12 vans | +5% | +6% | +14% | best |
| 14 vans | best | +21% | +23% | +5% |
| Morning rush 30 min earlier | +27% | +11% | +3% | best |
| Morning rush 60 min later | +58% | best | +56% | +49% |
| All times 60 min later | +68% | +72% | +2% | best |

The 125-minute limit has the lowest worst-case (49%) and mean (about 8%; 8.0%
from the rounded table above) gap. It
loses when the morning rush moves an hour later, and results can change by up
to 14% between 120 and 125 minutes on other fleet sizes.

## Rejected alternatives

- Morning cap (trips planned before 10:00 must return by 10:15): -17.6% vs the
  reference, but no van can leave 08:20-09:50, and it is 21% worse with 14 vans.
- Keeping 1-4 vans at the hub until 10:00: more undelivered parcels; -5.5% to +0.2%.
- Checking the waiting rule after 2-opt: never waits, identical to deadline + 2-opt.
- Waiting whenever leaving 10 minutes later lowers the route penalty: +1.1%.
- Sending urgent parcels during the morning cap's idle period: -0.3%; vans are
  rarely idle then.

Parameters were chosen on the same 20 days they are scored on; there is no
untouched evaluation set.
