"""Compare two policies day by day from their metrics.json files.

Usage: python3 compare_days.py <policy_A> <policy_B>
Reads results/<policy>/day_XXX/metrics.json for day_001 to day_020. Writes nothing.
"""

import json
import math
import statistics
import sys
from pathlib import Path

RESULTS = Path("results")
DAYS = [f"day_{i:03d}" for i in range(1, 21)]
SPLITS = [("all 20 days", DAYS), ("days 001-010", DAYS[:10]), ("days 011-020", DAYS[10:])]
MEASURES = [("total_early_minutes", "early minutes"), ("total_late_minutes", "late minutes"),
            ("undelivered_parcels", "undelivered"), ("number_of_trips", "trips")]
TIE = 1e-9  # penalties are rounded to 2 decimals, so only exact equality counts as a tie


def fail(message):
    """Print a clear error and stop, rather than skipping anything silently."""
    print(f"Error: {message}")
    sys.exit(1)


def load(policy):
    """Return {day: metrics} for one policy, stopping if any file is missing."""
    out = {}
    for day in DAYS:
        path = RESULTS / policy / day / "metrics.json"
        if not path.is_file():
            fail(f"missing {path}")
        out[day] = json.loads(path.read_text(encoding="utf-8"))
    return out


def winner(a, b):
    """Return 'A', 'B' or 'tie' for the lower of two values."""
    if abs(a - b) <= TIE:
        return "tie"
    return "A" if a < b else "B"


def sign_test(wins_a, wins_b):
    """Two-sided exact sign test p-value (binomial, p = 0.5) on non-tied days."""
    n = wins_a + wins_b
    if n == 0:
        return 1.0
    k = min(wins_a, wins_b)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 compare_days.py <policy_A> <policy_B>")
        sys.exit(1)
    name_a, name_b = sys.argv[1], sys.argv[2]
    a, b = load(name_a), load(name_b)
    print(f"A = {name_a}, B = {name_b}  (difference = B - A; lower penalty is better)\n")

    # 1. Daily total penalty table
    diff = {}
    print(f"{'day':<9}{'A penalty':>13}{'B penalty':>13}{'B - A':>12}{'% diff':>9}  lower")
    for day in DAYS:
        pa, pb = a[day]["total_penalty"], b[day]["total_penalty"]
        diff[day] = pb - pa
        pct = diff[day] / pa * 100 if pa else 0.0
        print(f"{day:<9}{pa:>13.2f}{pb:>13.2f}{diff[day]:>12.2f}{pct:>8.1f}%  {winner(pa, pb)}")

    # 2. Win counts and daily-difference summary for each split
    print(f"\n{'split':<14}{'A wins':>7}{'B wins':>7}{'ties':>6}{'mean B-A':>12}{'median B-A':>12}"
          f"  largest A win            largest B win")
    for label, days in SPLITS:
        results = [winner(a[d]["total_penalty"], b[d]["total_penalty"]) for d in days]
        diffs = [diff[d] for d in days]
        # A wins when B - A > 0; B wins when B - A < 0. Largest win = biggest margin.
        a_days = [d for d in days if diff[d] > TIE]
        b_days = [d for d in days if diff[d] < -TIE]
        best_a = max(a_days, key=lambda d: diff[d]) if a_days else None
        best_b = min(b_days, key=lambda d: diff[d]) if b_days else None
        a_text = f"{diff[best_a]:.2f} ({best_a})" if best_a else "-"
        b_text = f"{-diff[best_b]:.2f} ({best_b})" if best_b else "-"
        print(f"{label:<14}{results.count('A'):>7}{results.count('B'):>7}{results.count('tie'):>6}"
              f"{statistics.mean(diffs):>12.2f}{statistics.median(diffs):>12.2f}"
              f"  {a_text:<24} {b_text}")

    # 3. Exact two-sided sign test over all 20 days (ties dropped)
    results = [winner(a[d]["total_penalty"], b[d]["total_penalty"]) for d in DAYS]
    wins_a, wins_b = results.count("A"), results.count("B")
    p = sign_test(wins_a, wins_b)
    print(f"\nSign test (all 20 days, {results.count('tie')} ties dropped): "
          f"A {wins_a} vs B {wins_b} of n = {wins_a + wins_b}, two-sided p = {p:.4g}")

    # 4. Same daily comparison for the component measures
    print(f"\n{'measure':<16}{'B lower':>8}{'A lower':>8}{'ties':>6}{'mean B-A':>12}")
    for field, label in MEASURES:
        res = [winner(a[d][field], b[d][field]) for d in DAYS]
        mean_diff = statistics.mean(b[d][field] - a[d][field] for d in DAYS)
        print(f"{label:<16}{res.count('B'):>8}{res.count('A'):>8}{res.count('tie'):>6}"
              f"{mean_diff:>12.2f}")


if __name__ == "__main__":
    main()
