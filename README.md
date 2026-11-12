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
fleet is out wait less. This helps serve parcels that arrive during the 08:00-10:00 rush.
It uses no knowledge of future arrivals.

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

### Baseline

Single day, as in the project brief (simulate `day_001`, then score its log):

```bash
python3 -m simulator --policy solution.policies.baseline --data data --day day_001 --output results/baseline/day_001
python3 -m solution.performance_monitor --data data --day day_001 --log results/baseline/day_001/log.txt
```

These brief-style commands rewrite the saved `results/baseline/day_001` files. The baseline is deterministic, so they reproduce the saved files exactly (`python3 check_policy_replays.py --policy baseline` confirms this without writing anything).

All 20 days into a separate folder, then check every trip:

```bash
python3 run_all.py solution.policies.baseline replay_baseline
python3 check_trips.py replay_baseline
```

Single day into the separate folder:

```bash
python3 -m simulator --policy solution.policies.baseline --data data --day day_001 --output results/replay_baseline/day_001
python3 -m solution.performance_monitor --data data --day day_001 --log results/replay_baseline/day_001/log.txt
```

The saved baseline results are in `results/baseline/day_001` to `results/baseline/day_020`, each with a `log.txt` and a `metrics.json`.

`replay_*` folder names are used so that the submitted `results/<policy>/` folders are not overwritten.

### Selected policy

To run the selected policy for all 20 days and check its trips:

```bash
python3 run_all.py solution.policies.deadline_trip_limit replay_deadline_trip_limit
python3 check_trips.py replay_deadline_trip_limit
```

To run just one day:

```bash
python3 -m simulator --policy solution.policies.deadline_trip_limit --data data --day day_001 --output results/replay_deadline_trip_limit/day_001
python3 -m solution.performance_monitor --data data --day day_001 --log results/replay_deadline_trip_limit/day_001/log.txt
```

The `replay_` folder names above preserve the submitted results. Each run saves an event log (`log.txt`) and a metrics report (`metrics.json`)
in its policy and day folder. Repeating a run replaces those files.

Each policy keeps its own module and dispatch entry point. Shared construction,
waiting and local-search code is in `solution/policies/helpers.py`; policies do
not import one another.

See [reproduction commands](docs/reproduction.md) for all saved experiments and [the policy inventory](docs/policy_inventory.md) for every saved original-data variant. Run `python3 verify_results.py` to independently check saved scores, trips and protected files.

## Files

| Location | Contents |
|---|---|
| `data/` | Supplied demand, distances and configuration |
| `simulator/` | Supplied simulation framework |
| `solution/policies/` | Dispatch policies |
| `solution/policies/helpers.py` | Shared route builders, dispatch rules and local search |
| `solution/performance_monitor.py` | Penalty calculation and trip diagnostics |
| `results/` | Saved logs, daily metrics and experiment summaries |
| `docs/` | Experiment details, complexity analysis and run instructions |
| `experiments/` | Saved sweep, stress-study and runtime evidence |

The final report, [report.pdf](report.pdf), contains the findings, references and the record of AI assistance used in the project. See [supporting experiments](experiments/README.md) for the saved experiment records and their provenance.

## Further reading

- [Final report](report.pdf)
- [Trip limit experiment](docs/trip_limit_experiment.md)
- [Time and space complexity](docs/complexity_analysis.md)

## References

[1] Singapore Management University. (2026). IS115 project: Last-mile delivery planning [Project brief].

[2] Singapore Management University. (2026). Heuristics Part 2a: Greedy algorithms [IS115 Week 11 lecture slides].

[3] Singapore Management University. (2026). Heuristics Part 3: Local search [IS115 Week 11 lecture slides].

[4] Croes, G. A. (1958). A method for solving traveling-salesman problems. *Operations Research*, 6(6), 791–812.
