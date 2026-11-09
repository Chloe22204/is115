"""Replay saved policies and compare logs and metrics without replacing them."""

import argparse
import csv
import importlib
import io
import json
from pathlib import Path
import sys
from unittest.mock import patch

from simulator.loaders import day_input_paths
from simulator.simulator import Simulator
from solution.performance_monitor import calculate_metrics
from solution.policies.helpers import build_window_aligned_route


ROOT = Path(__file__).resolve().parent


class LogBuffer(io.StringIO):
    def __exit__(self, *args):
        # Simulator closes its output context before we compare the captured log.
        return False


def read_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def replay(policy, data, saved, day):
    parcel_path, distance_path, config_path = day_input_paths(data, day)
    simulator = Simulator(parcel_path, distance_path, config_path,
                          dispatch_policy=policy)
    buffer = LogBuffer()
    original_open = Path.open
    log_path = ROOT / "__replay_log_in_memory__"

    def capture_open(path, *args, **kwargs):
        if path == log_path:
            return buffer
        return original_open(path, *args, **kwargs)

    # Only the simulator's output is redirected. All input reads remain real.
    with patch.object(Path, "mkdir", return_value=None), \
            patch.object(Path, "open", capture_open):
        simulator.run(log_path)
    log = buffer.getvalue()
    if log.encode("utf-8") != (saved / day / "log.txt").read_bytes():
        raise AssertionError(f"Log differs: {saved} {day}")

    events = [json.loads(line) for line in log.splitlines() if line.strip()]
    metrics = calculate_metrics(
        read_rows(parcel_path), read_rows(distance_path),
        json.loads(config_path.read_text(encoding="utf-8-sig")), events,
    )
    report = json.dumps(metrics, indent=2, allow_nan=False) + "\n"
    if report.encode("utf-8") != (saved / day / "metrics.json").read_bytes():
        raise AssertionError(f"Metrics differ: {saved} {day}")


def fixed_120(parcels, context):
    departure = context["current_time"] + context["departure_delay"]
    limited = {**context, "return_cutoff": min(context["return_cutoff"], departure + 120.0)}
    return build_window_aligned_route(parcels, limited)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", action="append", help="check only this policy; repeat as needed")
    parser.add_argument("--stress", action="store_true", help="also replay all eight stress scenarios")
    args = parser.parse_args()
    names = args.policy or sorted(
        p.name for p in (ROOT / "results").iterdir()
        if p.is_dir() and any(p.glob("day_*/log.txt"))
    )
    original_runs = 0
    stress_runs = 0
    for name in names:
        dispatch = importlib.import_module("solution.policies." + name).dispatch
        for number in range(1, 21):
            replay(dispatch, ROOT / "data", ROOT / "results" / name,
                   f"day_{number:03d}")
            original_runs += 1
        print(f"Matched 20 logs and metrics: {name}", flush=True)

    if args.stress:
        study = ROOT / "experiments/robustness-study-2026-11-04"
        plan = json.loads((study / "plan.json").read_text())
        for scenario in plan["scenarios"]:
            scenario_name = scenario["name"]
            for name in plan["policies"]:
                dispatch = fixed_120 if name == "fixed_120" else importlib.import_module(
                    "solution.policies." + name).dispatch
                for number in range(1, 21):
                    replay(dispatch, study / "inputs" / scenario_name,
                           study / "results" / scenario_name / name,
                           f"day_{number:03d}")
                    stress_runs += 1
            print(f"Matched 100 stress logs and metrics: {scenario_name}", flush=True)
    print(json.dumps({"python": sys.version.split()[0], "policies": len(names),
                      "original_policy_days": original_runs,
                      "stress_policy_days": stress_runs,
                      "logs_and_metrics": "byte-identical"}), flush=True)


if __name__ == "__main__":
    main()
