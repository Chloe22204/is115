"""Sweep early/late penalty weights by re-scoring existing simulator logs.

Runs solution/performance_monitor.py on results/<policy>/day_XXX/log.txt for each scenario and
writes results_sweep/<scenario>/<policy>/<day>/metrics.json. Nothing under results/ is written.
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

RESULTS = Path("results")
DATA = Path("data")
SWEEP = Path("results_sweep")
DAYS = [f"day_{i:03d}" for i in range(1, 21)]
SCENARIOS = [(1, 1), (0.75, 1), (0.5, 1), (0.25, 1), (0, 1), (1, 2)]  # (early, late)
UNDELIVERED_PENALTY = 240.0
TOLERANCE = 0.02  # per-policy allowance for per-day rounding in metrics.json


def fail(message):
    """Print a clear error and stop, rather than skipping anything silently."""
    print(f"Error: {message}")
    sys.exit(1)


def scenario_name(early, late):
    """Folder name for a scenario, e.g. early0.5_late1."""
    return f"early{early:g}_late{late:g}"


def read_metrics(path):
    """Load one metrics.json, stopping if it is missing."""
    if not path.is_file():
        fail(f"missing {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def ranks(totals):
    """Return {policy: rank}, 1 = lowest total penalty (ties broken by name)."""
    order = sorted(totals, key=lambda p: (totals[p], p))
    return {policy: i + 1 for i, policy in enumerate(order)}


def main():
    # Policies are folders under results/ that contain day_XXX subfolders
    policies = sorted(p.name for p in RESULTS.iterdir()
                      if p.is_dir() and any(p.glob("day_*")))
    if not policies:
        fail(f"no policy folders found in {RESULTS}/")

    # Check every input up front so a missing file stops the run before any scoring
    for day in DAYS:
        if not (DATA / "demand" / f"{day}.csv").is_file():
            fail(f"missing {DATA / 'demand' / f'{day}.csv'}")
        for policy in policies:
            if not (RESULTS / policy / day / "log.txt").is_file():
                fail(f"missing {RESULTS / policy / day / 'log.txt'}")

    # 1. Score every policy and day under each scenario with the monitor
    totals = {}  # {scenario: {policy: summed total_penalty}}
    for early, late in SCENARIOS:
        name = scenario_name(early, late)
        totals[name] = {}
        for policy in policies:
            totals[name][policy] = 0.0
            for day in DAYS:
                out = SWEEP / name / policy / day / "metrics.json"
                cmd = [sys.executable, "-m", "solution.performance_monitor",
                       "--data", str(DATA), "--day", day,
                       "--log", str(RESULTS / policy / day / "log.txt"),
                       "--output", str(out),
                       "--early-weight", f"{early:g}", "--late-weight", f"{late:g}"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    fail(f"monitor failed for {name} {policy} {day}: {result.stderr.strip()}")
                totals[name][policy] += read_metrics(out)["total_penalty"]
    names = list(totals)
    rank = {name: ranks(totals[name]) for name in names}

    # 6. Scenario (1, 1) must reproduce the committed results/ totals
    base = scenario_name(1, 1)
    for policy in policies:
        committed = sum(read_metrics(RESULTS / policy / day / "metrics.json")["total_penalty"]
                        for day in DAYS)
        if abs(totals[base][policy] - committed) > TOLERANCE:
            fail(f"{base} total for {policy} is {totals[base][policy]:.2f}, "
                 f"committed results/ total is {committed:.2f}")
    print(f"Check passed: {base} matches committed results/ totals for all "
          f"{len(policies)} policies (within {TOLERANCE}).")

    # 2. One table per scenario, sorted by rank
    for name in names:
        print(f"\n{name}")
        print(f"  {'rank':<6}{'policy':<22}{'total penalty':>15}")
        for policy in sorted(policies, key=lambda p: rank[name][p]):
            print(f"  {rank[name][policy]:<6}{policy:<22}{totals[name][policy]:>15.2f}")

    # 3. Summary table of ranks: rows = policies, columns = scenarios
    width = max(len(n) for n in names) + 2
    print("\nRank summary (1 = lowest penalty)")
    print(f"{'policy':<22}" + "".join(f"{n:>{width}}" for n in names))
    for policy in policies:
        print(f"{policy:<22}" + "".join(f"{rank[n][policy]:>{width}}" for n in names))

    # 4. Same numbers (total and rank per scenario) to CSV
    with (SWEEP / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["policy"] + [f"{n}_{col}" for n in names for col in ("total", "rank")])
        for policy in policies:
            writer.writerow([policy] + [v for n in names
                                        for v in (f"{totals[n][policy]:.2f}", rank[n][policy])])
    print(f"\nWrote {SWEEP / 'summary.csv'}")

    # 5. Fine sweep: recombine the (1, 1) component sums instead of re-running the monitor.
    # penalty(w) = 240*U + w*E + L = A + w*E, with A = 240*U + L fixed per policy
    comp = {}
    for policy in policies:
        days = [read_metrics(SWEEP / base / policy / day / "metrics.json") for day in DAYS]
        u = sum(d["undelivered_parcels"] for d in days)
        e = sum(d["total_early_minutes"] for d in days)
        l = sum(d["total_late_minutes"] for d in days)
        comp[policy] = {"U": u, "E": e, "L": l, "A": UNDELIVERED_PENALTY * u + l}

    print("\nFine sweep, late weight 1: penalty(w) = 240*U + L + w*E = A + w*E")
    print(f"{'policy':<22}{'U':>7}{'E (early min)':>16}{'L (late min)':>15}{'A = 240U + L':>16}")
    for policy in policies:
        c = comp[policy]
        print(f"{policy:<22}{c['U']:>7}{c['E']:>16.2f}{c['L']:>15.2f}{c['A']:>16.2f}")

    # Grid w = 0, 0.05, ..., 1 (integer steps avoid floating-point drift)
    grid = [i / 20 for i in range(21)]
    best_at = {}
    for w in grid:
        best_at[w] = min(policies, key=lambda p: (comp[p]["A"] + w * comp[p]["E"], p))
    print("\nEarly-weight range (step 0.05) where each policy is ranked first:")
    for policy in policies:
        ws = [w for w in grid if best_at[w] == policy]
        if ws:
            print(f"  {policy:<22} w = {ws[0]:.2f} to {ws[-1]:.2f}  ({len(ws)} grid points)")
        else:
            print(f"  {policy:<22} never first")

    # Exact switch points: follow the lowest line from w = 0 up to w = 1.
    # A switch from policy i to j happens where A_i + w*E_i = A_j + w*E_j,
    # i.e. w = (A_j - A_i) / (E_i - E_j), which needs E_j < E_i.
    print("\nExact early weight at which the best policy changes:")
    w = 0.0
    current = min(policies, key=lambda p: (comp[p]["A"], comp[p]["E"], p))
    switches = 0
    while True:
        ci = comp[current]
        candidates = []
        for p in policies:
            cj = comp[p]
            if cj["E"] < ci["E"]:
                cross = (cj["A"] - ci["A"]) / (ci["E"] - cj["E"])
                if w < cross <= 1:
                    candidates.append((cross, p))
        if not candidates:
            break
        cross, nxt = min(candidates)
        cj = comp[nxt]
        print(f"  {current} -> {nxt}")
        print(f"    w = (A_{nxt} - A_{current}) / (E_{current} - E_{nxt})")
        print(f"      = ({cj['A']:.2f} - {ci['A']:.2f}) / ({ci['E']:.2f} - {cj['E']:.2f})")
        print(f"      = {cj['A'] - ci['A']:.2f} / {ci['E'] - cj['E']:.2f}")
        print(f"      = {cross:.4f}")
        print(f"    check: {current} {ci['A']:.2f} + {cross:.4f} x {ci['E']:.2f} = "
              f"{ci['A'] + cross * ci['E']:.2f};  {nxt} {cj['A']:.2f} + {cross:.4f} x "
              f"{cj['E']:.2f} = {cj['A'] + cross * cj['E']:.2f}")
        w, current = cross, nxt
        switches += 1
    if switches == 0:
        print(f"  none: {current} is first for every w in [0, 1]")


if __name__ == "__main__":
    main()
