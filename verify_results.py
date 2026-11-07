"""Check saved original-data scores, trips and protected files without writing outputs.

Run from any folder: python3 /path/to/G5T6/verify_results.py
This checks technical evidence, not report references or permission to use AI.
"""
import csv
import hashlib
import json
import math
import os
from pathlib import Path

import check_trips

ROOT = Path(__file__).resolve().parent


def read_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def minutes(value):
    hours, mins = map(int, value.split(":"))
    return hours * 60 + mins


def main():
    os.chdir(ROOT)
    protected = json.loads((ROOT / "docs/protected_files_sha256.json").read_text())
    for relative, expected in protected.items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Protected file changed: {relative}")
    config = json.loads((ROOT / "data/config.json").read_text())
    distances = check_trips.load_distances()
    folders = sorted(p for p in (ROOT / "results").iterdir()
                     if p.is_dir() and any(p.glob("day_*")))
    runs = 0
    checked_trips = 0
    for folder in folders:
        for number in range(1, 21):
            day = f"day_{number:03d}"
            demand = {p["parcel_id"]: p for p in read_rows(ROOT / "data/demand" / f"{day}.csv")}
            events = [json.loads(line) for line in (folder / day / "log.txt").read_text().splitlines() if line.strip()]
            recorded = json.loads((folder / day / "metrics.json").read_text())
            delivered = [e for e in events if e["event_type"] == "delivery"]
            ids = {e["parcel_id"] for e in delivered}
            if len(ids) != len(delivered) or not ids <= demand.keys():
                raise ValueError(f"Unknown or repeated delivery: {folder.name} {day}")
            early = math.fsum(max(0.0, minutes(demand[e["parcel_id"]]["delivery_window_start"]) - e["time"]) for e in delivered)
            late = math.fsum(max(0.0, e["time"] - minutes(demand[e["parcel_id"]]["delivery_window_end"])) for e in delivered)
            missed = len(demand) - len(ids)
            expected = {
                "total_parcels": len(demand), "delivered_parcels": len(ids),
                "undelivered_parcels": missed,
                "number_of_trips": sum(e["event_type"] == "hub_departure" for e in events),
                "delivery_rate_pct": round(100 * len(ids) / len(demand), 2),
                "total_early_minutes": round(early, 2),
                "total_late_minutes": round(late, 2),
                "total_penalty": round(240 * missed + early + late, 2),
            }
            for key, value in expected.items():
                # Summing floats in a different order can affect a cent at a rounding boundary.
                tolerance = 0.010001 if key in {"total_early_minutes", "total_late_minutes", "total_penalty"} else 0
                if not math.isfinite(recorded[key]) or abs(recorded[key] - value) > tolerance:
                    raise ValueError(f"Metric mismatch: {folder.name} {day} {key}")
            trips, errors = check_trips.check_day(folder.name, day, demand, distances, config)
            if errors:
                raise ValueError("\n".join(errors))
            checked_trips += trips
            runs += 1
    print(f"Verified {len(folders)} variants, {runs} policy-days and {checked_trips} trips.")
    print(f"All scores and hard constraints passed. {len(protected)} protected files match the supplied framework.")
    print("Report references, the assistance record and final ZIP contents require separate checks.")


if __name__ == "__main__":
    main()
