"""Rescore existing simulator logs with early deliveries unpenalised (--early-weight 0).

Reads results/<policy>/<day>/log.txt and writes results_experiment/<policy>/<day>/metrics.json.
Existing files under results/ are only read, never written.
"""

import json
import subprocess
import sys
from pathlib import Path

RESULTS = Path("results")
OUTPUT = Path("results_experiment")
DAYS = [f"day_{i:03d}" for i in range(1, 21)]
EARLY_WEIGHT = "0"


def fail(message):
    """Print a clear error and stop, rather than skipping anything silently."""
    print(f"Error: {message}")
    sys.exit(1)


def load_penalty(path):
    """Return total_penalty from a metrics.json file."""
    if not path.is_file():
        fail(f"missing {path}")
    return json.loads(path.read_text(encoding="utf-8"))["total_penalty"]


def ranking(totals):
    """Return policies ordered from lowest (best) to highest total penalty."""
    return sorted(totals, key=lambda policy: totals[policy])


def main():
    # Every subfolder of results/ is treated as one policy (benchmark.json etc. are skipped)
    policies = sorted(p.name for p in RESULTS.iterdir() if p.is_dir())
    if not policies:
        fail(f"no policy folders found in {RESULTS}/")

    original = {}
    experiment = {}
    for policy in policies:
        original[policy] = 0.0
        experiment[policy] = 0.0
        for day in DAYS:
            log = RESULTS / policy / day / "log.txt"
            if not log.is_file():
                fail(f"missing {log}")
            out = OUTPUT / policy / day / "metrics.json"

            # Rerun the monitor on the existing log with early minutes weighted 0
            cmd = [sys.executable, "-m", "solution.performance_monitor",
                   "--data", "data", "--day", day, "--log", str(log),
                   "--output", str(out), "--early-weight", EARLY_WEIGHT]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                fail(f"monitor failed for {policy} {day}: {result.stderr.strip()}")

            # Original score comes from the metrics.json already in results/
            original[policy] += load_penalty(RESULTS / policy / day / "metrics.json")
            experiment[policy] += load_penalty(out)

    # Table of 20-day totals under both metrics
    orig_rank = ranking(original)
    exp_rank = ranking(experiment)
    print(f"\n{'policy':<22}{'original':>12}{'rank':>6}{'early=0':>12}{'rank':>6}"
          f"{'change':>12}{'change %':>10}")
    for policy in orig_rank:
        change = experiment[policy] - original[policy]
        pct = change / original[policy] * 100 if original[policy] else 0.0
        print(f"{policy:<22}{original[policy]:>12.2f}{orig_rank.index(policy) + 1:>6}"
              f"{experiment[policy]:>12.2f}{exp_rank.index(policy) + 1:>6}"
              f"{change:>12.2f}{pct:>9.1f}%")

    print("\nRanking (best first)")
    print("  original:", " > ".join(orig_rank))
    print("  early=0: ", " > ".join(exp_rank))
    print("  ranking changed:", "yes" if orig_rank != exp_rank else "no")


if __name__ == "__main__":
    main()
