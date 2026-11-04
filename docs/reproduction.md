# Reproducing the results

Run these commands from the repository root using Python 3.9 or later. All
scripts use the standard library.

## Policies

Each command runs the simulator and performance monitor for all 20 days,
writing `results/<policy>/day_XXX/log.txt` and `metrics.json`. Running it again
replaces those outputs.

```bash
python3 run_all.py solution.policies.baseline baseline
python3 run_all.py solution.policies.deadline_window_departure deadline_window_departure
python3 run_all.py solution.policies.deadline_trip_limit deadline_trip_limit
```

## Inspect and compare results

These commands read saved results without rerunning the simulator:

```bash
python3 check_trips.py deadline_trip_limit deadline_window_departure
python3 compare_days.py deadline_trip_limit deadline_window_departure
python3 eval_split.py deadline_trip_limit deadline_window_departure
python3 analyze_floor.py
python3 analyze_baseline.py baseline
python3 analyze_late_parcels.py
```

## Penalty-weight sensitivity

These rescore saved logs under other weights and write to `results_sweep/`
and `results_experiment/`; nothing under `results/` is changed.

```bash
python3 sweep_weights.py
python3 rescore_experiment.py
```
