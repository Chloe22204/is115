# Reproducing the results

Use Python 3.9 or later and the standard library. Run commands from the submission folder containing `run_all.py`, `data/` and `solution/`. No connection to GitHub or Google Docs is needed.

## Baseline

```bash
python3 run_all.py solution.policies.baseline replay_baseline
python3 check_trips.py replay_baseline
```

The saved baseline results are in `results/baseline/day_XXX/`. The `replay_` commands above write to a new folder, `results/replay_baseline/`, which is created when you run them, so the saved results are not overwritten. After running the replay, to run the monitor separately on its first-day log:

```bash
python3 -m solution.performance_monitor --data data --day day_001 --log results/replay_baseline/day_001/log.txt
```

## Main comparison

Each command simulates all 20 supplied days and calculates daily metrics. Use a new output name to preserve the submitted results:

```bash
python3 run_all.py solution.policies.deadline_trip_limit replay_deadline_trip_limit
python3 check_trips.py replay_deadline_trip_limit
python3 compare_days.py replay_deadline_trip_limit deadline_trip_limit
```

The comparison should show equal daily penalties. To replay another policy, replace the module name and output folder. The nine main policies are:

```text
baseline
deadline_first
nearby_first
window_aware
nearby_local_search
nearby_two_opt
deadline_two_opt
deadline_window_departure
deadline_trip_limit
```

For example:

```bash
python3 run_all.py solution.policies.nearby_two_opt replay_nearby_two_opt
python3 check_trips.py replay_nearby_two_opt
```

## H1–H4 experiments

Run each variant using the same `run_all.py` command. Saved logs and metrics are under `results/<name>/day_XXX/`.

| Experiment | Policy modules |
|---|---|
| H1: urgency share, construction only | `hybrid_u0`, `hybrid_u25`, `hybrid_u50`, `hybrid_u75`, `hybrid_u100` |
| H1: urgency share with 2-opt | `nearby_two_opt` (U=0), `hybrid_u25_two_opt`, `hybrid_u50_two_opt`, `hybrid_u75_two_opt`, `hybrid_u100_two_opt` |
| H2: choose among candidate packings | `cand_p2_A`, `cand_p2_B`, `cand_p5_A`, `cand_p5_B` |
| H3: hold back future-window parcels | `holdback_h30`, `holdback_h60`, `holdback_h120` |
| H4: wait for a fuller trip | `wait_f50`, `wait_f70`, `wait_f90` |

For example:

```bash
python3 run_all.py solution.policies.cand_p2_A replay_cand_p2_A
python3 check_trips.py replay_cand_p2_A
```

`hybrid_u100_two_opt` and `deadline_two_opt` reproduce the same schedules. `holdback_h120` also matches these on the supplied days. The three H4 variants have identical saved schedules on these days.

## Complete saved inventory and independent checks

`docs/policy_inventory.md` lists every original-data variant and its total. Each has a separate module and 20 daily result pairs. Run any row through `run_all.py` using the same pattern above. These include backfill, exchange, relocation, return caps, size ties, morning-cap and reserve tests, and later fleet, slack and waiting variants.

```bash
python3 verify_results.py
```

This reads saved logs and independently checks scores, hard constraints and supplied-file hashes. It writes nothing and does not certify that references or the assistance record are complete.

## Check policy replays

```bash
python3 check_policy_replays.py
python3 check_policy_replays.py --stress
```

The first command replays all 57 original-data variants over 20 days. The second
also checks all 800 stress runs. Both compare generated logs and metrics
byte-for-byte with the saved files, without replacing them.

Shared policy code was moved into `solution/policies/helpers.py` on 9 November.
Policy names, entry points and algorithm settings are unchanged. The saved
runtime measurements predate this code reorganisation. They describe the
measured version, rather than a fresh timing of the refactored source.

## Trip-limit sweep

The original seven-setting validation, per-day results and split-half calculations are in `experiments/trip-limit-validation-2026-11-04/`.

```bash
python3 experiments/trip-limit-validation-2026-11-04/run_sweep.py
```

This reruns 140 policy-days and replaces that experiment's logs, metrics and summary. It checks eligibility, capacity, range, the trip limit and hub return. The 125-minute logs must match the submitted selected-policy logs.

All nine limits in the report can also be reproduced separately. For example:

```bash
python3 run_all.py solution.policies.trip_limit_100 replay_trip_limit_100
python3 run_all.py solution.policies.trip_limit_140 replay_trip_limit_140
```

The same module pattern covers 105, 110, 115, 120, 125, 130 and 135. These results are saved under `results/trip_limit_<minutes>/`. The seven-setting script above preserves its original scope.

## Worked 2-opt example

```bash
python3 experiments/worked-example/capture_example.py
```

This replays the selected policy over 20 days, checks the logs and records the reconstructed before/after route in `selected_example.json`. The initial order is a replay reconstruction. The final order and times match the saved log. This replaces that experiment's replay logs and selected example.

## Eight-scenario robustness study

Definitions are in `experiments/robustness-study-2026-11-04/plan.json`. Transformed inputs are kept inside that experiment, separate from the supplied `data/` folder. Five policies are compared on each scenario. `fixed_120` is defined inside `run_stress.py`.

```bash
python3 experiments/robustness-study-2026-11-04/prepare_inputs.py
python3 experiments/robustness-study-2026-11-04/run_stress.py original fleet_7 fleet_8 fleet_12 fleet_14 morning_arrivals_minus30 morning_arrivals_plus60 all_times_plus60
python3 experiments/robustness-study-2026-11-04/summarize.py
```

These commands regenerate the experiment's inputs and replace its results and summaries. The supplied data and policy sources are checked for changes. The original-scenario check also compares against the saved time-limit and return-tie trials under `experiments/` and the 120-minute sweep result.

This study has explicit transformations and a five-policy comparison pool. It is separate from Chloe's earlier stress summary. The scenarios reuse the same underlying 20 days and are not an unseen test set.

## Runtime measurement

Original measurements and their machine details are in `experiments/runtime/benchmark_results.json`. Retained logs are under `benchmark_logs/`.

```bash
python3 experiments/runtime/benchmark_current.py
```

This performs a full 20-day warm-up per policy, then three serial repetitions, reversing policy order in the middle repetition. It replaces the benchmark's timing file and retained logs. It checks replay logs against submitted results. Timing varies by machine and system load. Dispatch time measures policy calls, while replay time also includes simulation, loading, log writing and equality checks. Metric calculation and process startup are excluded.

## Read saved comparisons

These commands do not rerun policies:

```bash
python3 check_trips.py baseline deadline_window_departure deadline_trip_limit
python3 compare_days.py deadline_trip_limit deadline_window_departure
python3 eval_split.py deadline_trip_limit deadline_window_departure
python3 analyze_floor.py
python3 analyze_baseline.py baseline
python3 analyze_late_parcels.py
```

To reproduce the report's original 35-policy comparison directly from event logs:

```bash
python3 check_report_sensitivity.py
```

The pool is listed in `results/report_claim_checks.json`. The script checks early weights 0 and 1 at undelivered weights 120, 240 and 480, with late weight 1. Since each pairwise score difference is linear in early weight, endpoint dominance also establishes the result throughout [0, 1]. It does not claim the selected policy wins among all later trials.

For sensitivity across every currently saved original-data variant:

```bash
python3 sweep_weights.py
python3 rescore_experiment.py
```

These rescore existing schedules and write to `results_sweep/` and `results_experiment/`. They do not retune the policies.

## Evidence status

The experiment scripts and results were recovered from existing local files. Six scripts received path-only adjustments so they can use this submission folder. Historical findings are retained as dated notes and may refer to earlier folder locations or provisional recommendations. The current recommendation remains `deadline_trip_limit`.

The final report is `report.pdf`. Its references include the record of AI assistance used in the project.
