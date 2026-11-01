# IS115: Last-Mile Delivery Planning

This project compares delivery policies for a fleet of ten vans over 20 days.
The aim is to deliver more parcels within their preferred time windows while
working within vehicle capacity, range and operating hours.

## Selected policy

We recommend `deadline_window_departure`, which combines deadline-first
selection, a departure timing rule and 2-opt route improvement:

1. Build a feasible route, choosing parcels by earliest deadline, then distance.
2. Estimate when each parcel on that route would arrive. If every delivery is
   at least ten minutes early and delaying departure by ten minutes still allows
   a return by 18:00, leave the van idle for this planning round.
3. Otherwise, use 2-opt to improve the delivery order and dispatch the van.

A waiting van is reconsidered at the next planning round using the parcels
available then. The policy can wait even with a full load. It uses no knowledge
of future arrivals.

## Results

The dataset contains 15,867 parcels. Lower penalty is better.

| Policy | Parcels delivered | Total penalty |
|---|---:|---:|
| Baseline | 6,421 | 2,702,047.24 |
| Deadline-first | 15,206 | 355,647.04 |
| Nearby-first | 15,232 | 353,473.51 |
| Window-aware | 15,237 | 525,915.02 |
| Nearby + pair swaps | 15,175 | 328,603.53 |
| Nearby + 2-opt | 15,174 | 319,101.86 |
| Deadline + 2-opt | 15,177 | 255,466.93 |
| **Deadline + window-aligned departure + 2-opt** | **15,180** | **242,935.56** |

The selected policy reduces penalty by **4.91%** compared with deadline + 2-opt
and scores better on 16 of the 20 days. Most of the gain comes from reducing
early deliveries. Its median simulation time was 5.98 seconds, compared with
5.40 seconds for deadline + 2-opt in the same benchmark.

All 20 days were used during development, so these results do not establish
performance on unseen demand or prove that the policy is optimal.

## Scoring

```text
total penalty = 240 × undelivered parcels + early minutes + late minutes
```

For each delivered parcel, we count the minutes before its window opens or
after it closes. Deliveries within the window, including either boundary,
receive no timing penalty. Undelivered parcels receive only the fixed penalty
of 240.

We chose 240 to balance completed deliveries against timing: one undelivered
parcel costs the same as 240 minutes outside delivery windows. This is a
modelling choice, not a monetary cost supplied in the dataset. We also compared
results using other weights; see the [sensitivity results](docs/followup_search_results.md#sensitivity).

## Running the project

Use Python 3.9 or later. No additional packages are needed. Run the commands
from the repository folder containing `run_all.py`, `data/` and `solution/`.

To run the selected policy for all 20 days and check its trips:

```bash
python3 run_all.py solution.policies.deadline_window_departure deadline_window_departure
python3 check_trips.py deadline_window_departure
```

To run just one day:

```bash
python3 -m simulator --policy solution.policies.deadline_window_departure --data data --day day_001 --output results/deadline_window_departure/day_001
python3 -m solution.performance_monitor --data data --day day_001 --log results/deadline_window_departure/day_001/log.txt
```

Each run saves an event log (`log.txt`) and a metrics report (`metrics.json`)
in its policy and day folder. Repeating a run replaces those files.

See [reproduction commands](docs/reproduction.md) to run the baseline, other
policies, benchmarks and sensitivity checks.

## Files

| Location | Contents |
|---|---|
| `data/` | Supplied demand, distances and configuration |
| `simulator/` | Supplied simulation framework |
| `solution/policies/` | Dispatch policies |
| `solution/policies/helpers.py` | Shared route evaluation and 2-opt functions |
| `solution/performance_monitor.py` | Penalty calculation and trip diagnostics |
| `results/` | Saved logs, daily metrics and experiment summaries |
| `docs/` | Experiment details, complexity analysis and run instructions |
| `ai_log.md` | AI assistance record |

## Further reading

- [Report draft for team review](docs/report_draft.md)
- [Initial comparisons and four selection/waiting hypotheses](docs/experiment_notes.md)
- [Follow-up tests and the selected policy](docs/followup_search_results.md)
- [Time and space complexity](docs/complexity_analysis.md)
- [Return-time cap experiment](docs/return_time_cap_experiment.md)
- [Small-case exhaustive diagnosis](docs/small_case_diagnosis.md)
- [Insertion/backfill experiment](docs/backfill_experiment.md)
