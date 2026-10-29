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
python3 run_all.py solution.policies.deadline_two_opt deadline_two_opt
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
| `deadline_two_opt` | Deadline-first followed by the same best-improvement segment reversals |

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
| Deadline + 2-opt | 15,177 | 95.65% | 255,466.93 |

Deadline + 2-opt (`deadline_two_opt`) is the recommendation: it has the lowest
aggregate penalty in this table and a lower daily penalty than nearby + 2-opt on
all 20 days. These are comparisons on the same historical days used during
development, not a guarantee of optimality or performance on unseen demand.

The recommendation changed after the initial comparison. Nearby + 2-opt was the
initial provisional recommendation: among the first six policies it had the
lowest aggregate penalty and beats pair swaps on 19 of 20 days. It also ranks
first among them at weights 120 and 480. Deadline + 2-opt was tested afterwards
(see [Further hypotheses tested](#further-hypotheses-tested)) and had a lower
penalty than nearby + 2-opt on every one of the 20 days, so it replaced it.

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

## Sensitivity analysis

These scripts re-score the saved logs in `results/` without re-running any
simulation, and never modify `results/`.

```bash
python3 rescore_experiment.py
python3 analyze_late_parcels.py
python3 sweep_weights.py
```

- `rescore_experiment.py` re-scores every policy with early deliveries
  unpenalised (`--early-weight 0`), writes `results_experiment/`, and prints
  each policy's 20-day total and rank next to the original metric.
- `analyze_late_parcels.py` prints, per policy, how many delivered parcels were
  late and by more than 60, 120 and 240 minutes, the late minutes involved and
  their share of the main metric.
- `sweep_weights.py` scores every policy under several early/late weight
  scenarios into `results_sweep/` (with `results_sweep/summary.csv`), and finds
  the early weight at which the best policy changes.

`solution/performance_monitor.py` accepts `--early-weight` and `--late-weight`
(both default 1.0); with the defaults its output is unchanged.

## Further hypotheses tested

After the initial comparison, four further hypotheses were tested against the
same 20 days. Figures are 20-day total penalties from `results/`.

| Hypothesis | Modules | 20-day total penalty | Outcome |
|---|---|---:|---|
| Urgency selection + 2-opt: fill by deadline up to U × capacity, then by distance, then 2-opt | `deadline_two_opt` (U = 1), `hybrid_u75_two_opt`, `hybrid_u50_two_opt`, `hybrid_u25_two_opt` | 255,467 (`deadline_two_opt`) | Adopted: `deadline_two_opt` |
| Candidate selection: build several 2-opt routes per dispatch and keep the best-scoring one | `cand_p2_A`, `cand_p2_B`, `cand_p5_A`, `cand_p5_B` | 288,652 to 304,815 | Not adopted |
| Hold-back: hold parcels whose window opens more than H minutes after the van could arrive | `holdback_h30`, `holdback_h60`, `holdback_h120` | 260,252 (H = 60) | Not adopted |
| Wait-to-fill: keep an under-filled van at the hub for up to 30 minutes | `wait_f50`, `wait_f70`, `wait_f90` | 252,768 | Rejected under the pre-set rule |

Wait-to-fill has the lowest 20-day total, but has a lower penalty than
`deadline_two_opt` on only 12 of 20 days (sign test p = 0.50) and a higher total
on days 001-010. Its three F values produce identical logs. Hold-back with
H = 120 produces logs identical to `deadline_two_opt`. Details, sign tests and
limitations are in the [experiment notes](docs/experiment_notes.md).

Regenerate each set of results (each command runs all 20 days):

```bash
# Urgency selection + 2-opt
python3 run_all.py solution.policies.deadline_two_opt deadline_two_opt
python3 run_all.py solution.policies.hybrid_u75_two_opt hybrid_u75_two_opt
python3 run_all.py solution.policies.hybrid_u50_two_opt hybrid_u50_two_opt
python3 run_all.py solution.policies.hybrid_u25_two_opt hybrid_u25_two_opt
# Candidate selection
python3 run_all.py solution.policies.cand_p2_A cand_p2_A
python3 run_all.py solution.policies.cand_p2_B cand_p2_B
python3 run_all.py solution.policies.cand_p5_A cand_p5_A
python3 run_all.py solution.policies.cand_p5_B cand_p5_B
# Hold-back
python3 run_all.py solution.policies.holdback_h30 holdback_h30
python3 run_all.py solution.policies.holdback_h60 holdback_h60
python3 run_all.py solution.policies.holdback_h120 holdback_h120
# Wait-to-fill
python3 run_all.py solution.policies.wait_f50 wait_f50
python3 run_all.py solution.policies.wait_f70 wait_f70
python3 run_all.py solution.policies.wait_f90 wait_f90
```

Compare and check saved results without re-running simulations:

```bash
python3 eval_split.py deadline_two_opt nearby_two_opt   # totals for days 001-010 and 011-020
python3 compare_days.py deadline_two_opt nearby_two_opt # daily comparison and sign test
python3 check_trips.py deadline_two_opt                 # capacity, range, cutoff and parcel checks
```
