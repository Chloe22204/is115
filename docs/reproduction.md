# Reproducing the experiments

Run these commands from the repository root using Python 3.9 or later. All
scripts use the standard library.

## Saved policy variants

Each command runs the simulator and performance monitor for all 20 days,
writing `results/<policy>/day_XXX/log.txt` and `metrics.json`. Running it again
replaces those outputs. The list includes all 34 saved variants; parameter
variants are not 34 distinct algorithm families.

```bash
python3 run_all.py solution.policies.baseline baseline
python3 run_all.py solution.policies.cand_p2_A cand_p2_A
python3 run_all.py solution.policies.cand_p2_B cand_p2_B
python3 run_all.py solution.policies.cand_p5_A cand_p5_A
python3 run_all.py solution.policies.cand_p5_B cand_p5_B
python3 run_all.py solution.policies.deadline_backfill deadline_backfill
python3 run_all.py solution.policies.deadline_cap0 deadline_cap0
python3 run_all.py solution.policies.deadline_cap15 deadline_cap15
python3 run_all.py solution.policies.deadline_cap30 deadline_cap30
python3 run_all.py solution.policies.deadline_exchange deadline_exchange
python3 run_all.py solution.policies.deadline_first deadline_first
python3 run_all.py solution.policies.deadline_relocate deadline_relocate
python3 run_all.py solution.policies.deadline_size_ties deadline_size_ties
python3 run_all.py solution.policies.deadline_two_opt deadline_two_opt
python3 run_all.py solution.policies.deadline_window_departure deadline_window_departure
python3 run_all.py solution.policies.holdback_h120 holdback_h120
python3 run_all.py solution.policies.holdback_h30 holdback_h30
python3 run_all.py solution.policies.holdback_h60 holdback_h60
python3 run_all.py solution.policies.hybrid_u0 hybrid_u0
python3 run_all.py solution.policies.hybrid_u100 hybrid_u100
python3 run_all.py solution.policies.hybrid_u100_two_opt hybrid_u100_two_opt
python3 run_all.py solution.policies.hybrid_u25 hybrid_u25
python3 run_all.py solution.policies.hybrid_u25_two_opt hybrid_u25_two_opt
python3 run_all.py solution.policies.hybrid_u50 hybrid_u50
python3 run_all.py solution.policies.hybrid_u50_two_opt hybrid_u50_two_opt
python3 run_all.py solution.policies.hybrid_u75 hybrid_u75
python3 run_all.py solution.policies.hybrid_u75_two_opt hybrid_u75_two_opt
python3 run_all.py solution.policies.nearby_first nearby_first
python3 run_all.py solution.policies.nearby_local_search nearby_local_search
python3 run_all.py solution.policies.nearby_two_opt nearby_two_opt
python3 run_all.py solution.policies.wait_f50 wait_f50
python3 run_all.py solution.policies.wait_f70 wait_f70
python3 run_all.py solution.policies.wait_f90 wait_f90
python3 run_all.py solution.policies.window_aware window_aware
```

## Inspect and compare results

These commands read saved results without rerunning the simulator:

```bash
python3 analyze_baseline.py deadline_window_departure
python3 eval_split.py deadline_window_departure deadline_two_opt
python3 compare_days.py deadline_window_departure deadline_two_opt
python3 check_trips.py deadline_window_departure deadline_two_opt
```

Despite its name, `analyze_baseline.py` accepts any policy result-folder name.
It reports operational diagnostics. The chosen penalty is in `metrics.json`.
`eval_split.py` compares days 1–10 and 11–20; `compare_days.py` gives daily
comparisons and a sign test. `check_trips.py` checks logged trips against
capacity, range, return time and parcel eligibility constraints.

## Runtime measurements

```bash
python3 benchmark_policies.py
python3 benchmark_followups.py
```

The first script benchmarks the original comparison; the second benchmarks the
follow-up policies. Each uses a day-1 warm-up, then three repetitions of all
20 days, alternating policy order. They write `results/benchmark.json` and
`results/followup_benchmark.json`, respectively. Rerunning replaces those
benchmark files. Replay logs are temporary; saved daily experiment logs and
metrics are unchanged.

Total simulation time includes construction, input loading, snapshot copying,
event processing and logging. Dispatch time measures execution inside the
policy. Neither includes metric calculation or interpreter startup. Runtime
varies with the machine and system load.

## Sensitivity analysis

```bash
python3 rescore_experiment.py
python3 analyze_late_parcels.py
python3 sweep_weights.py
```

These scripts use saved results without rerunning simulations.

- `rescore_experiment.py` removes early-delivery penalties and writes rescored
  reports to `results_experiment/`.
- `analyze_late_parcels.py` reports late deliveries and their contribution to
  each policy's penalty.
- `sweep_weights.py` compares several early/late weight combinations and writes
  `results_sweep/`, including `summary.csv`.

The monitor also accepts `--early-weight` and `--late-weight`, both defaulting
to 1. These scripts rescore fixed policies; they do not retune the algorithms.

## Bounded diagnosis

```bash
python3 -B diagnose_small_cases.py
```

This replays selected reference-policy days and enumerates ordered subsets of
small parcel pools. It writes `results/small_case_diagnosis.json`. See the
[diagnosis notes](small_case_diagnosis.md) for the sampling rules and limits.
