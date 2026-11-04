# IS115: Last-Mile Delivery Planning

This project compares delivery policies for a fleet of ten vans over 20 days.
The aim is to deliver more parcels within their preferred time windows while
working within vehicle capacity, range and operating hours.

## Selected policy

We recommend `deadline_trip_limit`, which builds on deadline-first selection,
a departure timing rule and 2-opt route improvement:

1. Build a feasible route, choosing parcels by earliest deadline, then distance.
   Every trip must be back at the hub within 125 minutes of leaving.
2. Estimate when each parcel on that route would arrive. If every delivery is
   at least ten minutes early and delaying departure by ten minutes still allows
   a return within the limit, leave the van idle for this planning round.
3. Otherwise, use 2-opt to improve the delivery order and dispatch the van.

Short trips bring vans back to the hub often, so parcels that arrive while the
fleet is out wait less. This matters most for the 08:00-10:00 rush, whose
windows close at 10:00-11:00. It uses no knowledge of future arrivals.

## Results

The dataset contains 15,867 parcels. Lower penalty is better.

| Policy | Parcels delivered | Total penalty |
|---|---:|---:|
| Baseline | 6,421 | 2,702,047.24 |
| Deadline + window-aligned departure + 2-opt | 15,180 | 242,935.56 |
| **+ 125-minute trip limit** | **15,222** | **179,088.70** |

The trip limit reduces penalty by **26.3%** compared with
`deadline_window_departure` and is no worse on any of the 20 days. Limits from
105 to 130 minutes all score well. See [the trip limit experiment](docs/trip_limit_experiment.md).

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
modelling choice, not a monetary cost supplied in the dataset. `sweep_weights.py` rescores saved logs under other weights.

## Running the project

Use Python 3.9 or later. No additional packages are needed. Run the commands
from the repository folder containing `run_all.py`, `data/` and `solution/`.

To run the selected policy for all 20 days and check its trips:

```bash
python3 run_all.py solution.policies.deadline_trip_limit deadline_trip_limit
python3 check_trips.py deadline_trip_limit
```

To run just one day:

```bash
python3 -m simulator --policy solution.policies.deadline_trip_limit --data data --day day_001 --output results/deadline_trip_limit/day_001
python3 -m solution.performance_monitor --data data --day day_001 --log results/deadline_trip_limit/day_001/log.txt
```

Each run saves an event log (`log.txt`) and a metrics report (`metrics.json`)
in its policy and day folder. Repeating a run replaces those files.

See [reproduction commands](docs/reproduction.md) to run the baseline, the reference policy and the analysis scripts.

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
- [Trip limit experiment](docs/trip_limit_experiment.md)
- [Time and space complexity](docs/complexity_analysis.md)
