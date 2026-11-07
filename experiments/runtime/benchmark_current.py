"""Serial, in-process benchmark of the three retained comparison policies."""
import hashlib
import importlib
import json
import os
import platform
from pathlib import Path
import statistics
import sys
from time import perf_counter

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))
from simulator.simulator import Simulator
from simulator.loaders import day_input_paths

POLICIES = ["baseline", "deadline_window_departure", "deadline_trip_limit"]

def run_policy(name, repetition):
    policy = importlib.import_module("solution.policies." + name).dispatch
    policy_seconds = 0.0
    calls = 0
    def timed_policy(parcels, context):
        nonlocal policy_seconds, calls
        calls += 1
        before = perf_counter()
        try:
            return policy(parcels, context)
        finally:
            policy_seconds += perf_counter() - before
    before = perf_counter()
    matches = []
    for i in range(1, 21):
        day = f"day_{i:03d}"
        log = HERE / "benchmark_logs" / name / day / "log.txt"
        sim = Simulator(*day_input_paths(REPO / "data", day), dispatch_policy=timed_policy)
        sim.run(log)
        saved = REPO / "results" / name / day / "log.txt"
        matches.append(log.read_bytes() == saved.read_bytes())
    total_seconds = perf_counter() - before
    if not all(matches):
        raise AssertionError((name, repetition, matches))
    result = dict(policy=name, repetition=repetition, total_seconds=total_seconds,
                  policy_seconds=policy_seconds, dispatch_calls=calls,
                  milliseconds_per_call=1000 * policy_seconds / calls,
                  exact_log_matches=sum(matches))
    print(json.dumps(result), flush=True)
    return result

def main():
    sources = {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in list((REPO / "solution/policies").glob("*.py")) +
               list((REPO / "simulator").glob("*.py"))}
    warmup = [run_policy(name, "warmup") for name in POLICIES]
    samples = []
    for repetition in range(1, 4):
        order = list(reversed(POLICIES)) if repetition == 2 else POLICIES
        samples.extend(run_policy(name, repetition) for name in order)
    medians = {}
    for name in POLICIES:
        rows = [r for r in samples if r["policy"] == name]
        medians[name] = {key: statistics.median(r[key] for r in rows)
                         for key in ["total_seconds", "policy_seconds", "dispatch_calls", "milliseconds_per_call"]}
    for relative, digest in sources.items():
        assert hashlib.sha256((REPO / relative).read_bytes()).hexdigest() == digest
    result = dict(method="One full-20-day warm-up per policy, then three serial full-20-day repetitions; reverse policy order in repetition 2. Total includes input loading, simulator and log writing, plus equality-check overhead; excludes process startup and metric calculation. Dispatch time uses a perf_counter wrapper. No claim of an otherwise idle host.",
                  machine=dict(platform=platform.platform(), machine=platform.machine(), processor=platform.processor(), logical_cpu_count=os.cpu_count(), python=sys.version),
                  sources_sha256=sources, warmup=warmup, samples=samples, medians=medians)
    (HERE / "benchmark_results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(dict(medians=medians, machine=result["machine"])), flush=True)

if __name__ == "__main__":
    main()
