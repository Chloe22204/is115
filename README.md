# IS115: Last-Mile Delivery Planning

Compare dispatch policies on the supplied 20-day parcel dataset. Run commands
from this directory (`Project/GitHub`), using Python 3.9 or later. All policies
and helper scripts use the Python standard library.

## Performance metric

Lower is better:

```text
total penalty = 240 × undelivered parcels + total early minutes + total late minutes
```

For a delivered parcel, early minutes are `max(0, window_start - delivery_time)`
and late minutes are `max(0, delivery_time - window_end)`. An undelivered parcel
receives only the fixed penalty of 240. Delivery at either window boundary is
within the window. Times are converted to minutes after midnight.

The weight 240 expresses the team's chosen trade-off: one undelivered parcel
is equivalent to 240 accumulated minutes outside preferred windows. It is not
a supplied business cost. Results are also checked at weights 120 and 480.

## Reproduce one day

```bash
python3 -m simulator --policy solution.policies.baseline --data data --day day_001 --output results/baseline/day_001
python3 -m solution.performance_monitor --data data --day day_001 --log results/baseline/day_001/log.txt
```

The simulator writes `log.txt`. The monitor writes `metrics.json` alongside it,
including parcel counts, delivery rate, timing penalties and trip capacity
diagnostics. Repeating commands replaces outputs at those paths.

## Reproduce all experiments

Each command runs both the simulator and performance monitor for all 20 days:

```bash
python3 run_all.py solution.policies.baseline baseline
python3 run_all.py solution.policies.deadline_first deadline_first
python3 run_all.py solution.policies.nearby_first nearby_first
python3 run_all.py solution.policies.window_aware window_aware
python3 run_all.py solution.policies.nearby_local_search nearby_local_search
python3 run_all.py solution.policies.nearby_two_opt nearby_two_opt
```

To inspect existing runs without changing them:

```bash
python3 analyze_baseline.py baseline
python3 analyze_baseline.py nearby_two_opt
```

Despite its filename, `analyze_baseline.py` accepts any of the result-folder names.
It reports operational diagnostics; the chosen penalty is in `metrics.json`.

## Policy definitions

| Module | Selection or improvement rule |
|---|---|
| `baseline` | Arrival order; skip additions that violate hard constraints |
| `deadline_first` | Earliest window end, then distance from current location, then parcel ID |
| `nearby_first` | Distance from current location, then window end, then parcel ID |
| `window_aware` | Travel minutes plus predicted early/late minutes; ties use distance, window end, parcel ID |
| `nearby_local_search` | Nearby-first followed by best-improvement parcel-pair swaps |
| `nearby_two_opt` | Nearby-first followed by best-improvement segment reversals |

All routes respect capacity, round-trip range and the 18:00 hub-return deadline.
Policies use only the supplied snapshots, never read future demand, and do not
mutate their inputs. Early/late deliveries remain allowed. The two local-search
policies keep each initial route's selected parcels and optimise its timing
penalty, stopping when no feasible improving move exists. Later trips can change
because route changes affect vehicle availability.

## Results on the supplied 20 days

There are 15,867 parcels. Scores sum the reported daily penalties.

| Policy | Delivered | Delivery rate | Total penalty |
|---|---:|---:|---:|
| Baseline | 6,421 | 40.47% | 2,702,047.24 |
| Deadline-first | 15,206 | 95.83% | 355,647.04 |
| Nearby-first | 15,232 | 96.00% | 353,473.51 |
| Window-aware | 15,237 | 96.03% | 525,915.02 |
| Nearby + pair swaps | 15,175 | 95.64% | 328,603.53 |
| Nearby + 2-opt | 15,174 | 95.63% | 319,101.86 |

Nearby + 2-opt is the provisional recommendation: it has the lowest aggregate
penalty and beats pair swaps on 19 of 20 days. It also ranks first at weights
120 and 480. These are comparisons on the same historical days used during
development, not a guarantee of optimality or performance on unseen demand.

See [experiment notes](docs/experiment_notes.md) for explanations, sensitivity
results, complexity assumptions and remaining report work.

## Runtime measurements

```bash
python3 benchmark_policies.py
```

This runs one day-1 warm-up per policy, then three measured repetitions of all
20 days. It alternates policy order between repetitions and writes
`results/benchmark.json`. Simulation logs are temporary; saved experiment logs
and daily metrics are not changed. Running again replaces the benchmark file.

Total time includes simulator construction, input loading, input snapshots,
event processing and temporary logging. Dispatch time measures only execution
inside the policy. Neither includes the performance-monitor calculation or
Python command-line startup. Results vary with machine and system load.

## Project files and references

Keep supplied `data/`, `simulator/`, `baseline.py` and package `__init__.py`
files unchanged. New policies live in `solution/policies/`; the chosen metric
is in `solution/performance_monitor.py`.

`ai_log.md` records assistance. Complete its outstanding prompt/response entries
and reconcile the record with actual tool use before preparing the references.
The final report must also cite the brief and the course material used for
greedy construction and local search.
