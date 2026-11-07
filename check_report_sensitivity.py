"""Reproduce Section 5.6's original 35-policy sensitivity comparison from logs.

The pool is explicit: later challengers and the separate trip-limit sweep are
excluded. Endpoint checks establish each pairwise linear comparison for every
early-minute weight between zero and one, with late-minute weight fixed at one.
"""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def minutes(value):
    hours, mins = map(int, value.split(":"))
    return 60 * hours + mins


def main():
    pool = json.loads((ROOT / "results/report_claim_checks.json").read_text())["original_35_policy_pool"]
    if len(pool) != 35:
        raise ValueError("The original comparison pool must contain 35 policies")
    components = {name: {"U": 0, "E": [], "L": []} for name in pool}
    for number in range(1, 21):
        day = f"day_{number:03d}"
        with (ROOT / "data/demand" / f"{day}.csv").open(newline="", encoding="utf-8-sig") as stream:
            demand = {p["parcel_id"]: p for p in csv.DictReader(stream)}
        for name in pool:
            events = [json.loads(line) for line in (ROOT / "results" / name / day / "log.txt").read_text().splitlines() if line.strip()]
            delivered = [e for e in events if e["event_type"] == "delivery"]
            if len({e["parcel_id"] for e in delivered}) != len(delivered):
                raise ValueError(f"Repeated delivery: {name} {day}")
            components[name]["U"] += len(demand) - len(delivered)
            components[name]["E"].extend(max(0.0, minutes(demand[e["parcel_id"]]["delivery_window_start"]) - e["time"]) for e in delivered)
            components[name]["L"].extend(max(0.0, e["time"] - minutes(demand[e["parcel_id"]]["delivery_window_end"])) for e in delivered)
    for values in components.values():
        values["E"] = math.fsum(values["E"])
        values["L"] = math.fsum(values["L"])
    for missed_weight in [120, 240, 480]:
        for early_weight in [0, 1]:
            scores = {name: missed_weight * c["U"] + early_weight * c["E"] + c["L"] for name, c in components.items()}
            winner = min(scores, key=scores.get)
            if winner != "deadline_trip_limit":
                raise ValueError(f"Unexpected winner: {winner}")
            print(f"Undelivered weight {missed_weight}, early weight {early_weight}: {winner}, {scores[winner]:,.2f}")
    print("Passed for the original 35-policy pool. Later candidates are a separate comparison.")


if __name__ == "__main__":
    main()
