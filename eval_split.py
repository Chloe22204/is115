"""Sum metrics for days 001-010 and 011-020 separately, per policy.

Usage: python3 eval_split.py [policy ...]   (default: every policy folder under results/)
Reads results/<policy>/day_XXX/metrics.json only. Writes nothing.
"""

import json
import sys
from pathlib import Path

RESULTS = Path("results")
SPLITS = {
    "001-010": [f"day_{i:03d}" for i in range(1, 11)],
    "011-020": [f"day_{i:03d}" for i in range(11, 21)],
}


def fail(message):
    """Print a clear error and stop, rather than skipping anything silently."""
    print(f"Error: {message}")
    sys.exit(1)


def split_totals(policy, days):
    """Sum penalty, undelivered, early and late minutes over the given days."""
    totals = {"penalty": 0.0, "undelivered": 0, "early": 0.0, "late": 0.0}
    for day in days:
        path = RESULTS / policy / day / "metrics.json"
        if not path.is_file():
            fail(f"missing {path}")
        m = json.loads(path.read_text(encoding="utf-8"))
        totals["penalty"] += m["total_penalty"]
        totals["undelivered"] += m["undelivered_parcels"]
        totals["early"] += m["total_early_minutes"]
        totals["late"] += m["total_late_minutes"]
    return totals


def main():
    # Policies from the command line, or every folder under results/ with day_XXX subfolders
    if len(sys.argv) > 1:
        policies = sys.argv[1:]
        for policy in policies:
            if not (RESULTS / policy).is_dir():
                fail(f"no results folder {RESULTS / policy}")
    else:
        policies = sorted(p.name for p in RESULTS.iterdir()
                          if p.is_dir() and any(p.glob("day_*")))
    if not policies:
        fail(f"no policy folders found in {RESULTS}/")

    # One row per policy and split
    width = max(len(p) for p in policies) + 2
    print(f"{'policy':<{width}}{'days':<10}{'total penalty':>15}{'undelivered':>13}"
          f"{'early min':>12}{'late min':>12}")
    for policy in policies:
        for split, days in SPLITS.items():
            t = split_totals(policy, days)
            print(f"{policy:<{width}}{split:<10}{t['penalty']:>15.2f}{t['undelivered']:>13}"
                  f"{t['early']:>12.2f}{t['late']:>12.2f}")


if __name__ == "__main__":
    main()
