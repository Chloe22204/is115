"""Benchmark and replay-check the reference and window-aligned departure policy."""

import json
import platform
import statistics
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from simulator.simulator import Simulator, load_policy


def main():
    names = ["deadline_two_opt", "deadline_window_departure"]
    policies = {name: load_policy("solution.policies." + name) for name in names}
    records = []
    with TemporaryDirectory(prefix="is115-followup-benchmark-") as directory:
        log = Path(directory) / "log.txt"
        for name in names:
            sim = Simulator("data/demand/day_001.csv", "data/dist.csv", "data/config.json",
                            dispatch_policy=policies[name])
            sim.run(log)
        for repetition in range(3):
            for name in names if repetition % 2 == 0 else reversed(names):
                policy_seconds = 0.0
                calls = 0

                def measured(parcels, context):
                    nonlocal policy_seconds, calls
                    start = time.perf_counter()
                    try:
                        return policies[name](parcels, context)
                    finally:
                        policy_seconds += time.perf_counter() - start
                        calls += 1

                total_seconds = 0.0
                delivered = 0
                for day_number in range(1, 21):
                    day = f"day_{day_number:03d}"
                    start = time.perf_counter()
                    sim = Simulator(f"data/demand/{day}.csv", "data/dist.csv", "data/config.json",
                                    dispatch_policy=measured)
                    sim.run(log)
                    total_seconds += time.perf_counter() - start
                    delivered += len(sim.delivered)
                    # Readback verification is outside the measured interval.
                    assert log.read_bytes() == Path(f"results/{name}/{day}/log.txt").read_bytes(), (name, day)
                record = dict(policy=name, repetition=repetition + 1, total_seconds=total_seconds,
                              policy_seconds=policy_seconds, dispatch_calls=calls, delivered=delivered)
                records.append(record)
                print(json.dumps(record), flush=True)
    summary = []
    for name in names:
        rows = [r for r in records if r["policy"] == name]
        assert len({r["delivered"] for r in rows}) == 1
        summary.append(dict(policy=name,
                            median_total_seconds=statistics.median(r["total_seconds"] for r in rows),
                            median_policy_seconds=statistics.median(r["policy_seconds"] for r in rows)))
    result = dict(environment=dict(python=sys.version, platform=platform.platform()),
                  method="Day-1 warm-up; three 20-day repetitions; alternate policy order. Times exclude metric calculation, interpreter startup and replay-file comparison.",
                  records=records, summary=summary)
    Path("results/followup_benchmark.json").write_text(json.dumps(result, indent=2) + "\n")
    print("SUMMARY", json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
