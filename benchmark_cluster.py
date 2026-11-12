"""Time dispatch calls of the seed-and-cluster variants against deadline_trip_limit.

Same method as benchmark_policies.py: 3 repetitions x 20 days, alternating order,
after one warm-up day. Writes results/cluster_benchmark.json only.
"""
import json, statistics, time
from pathlib import Path
from tempfile import TemporaryDirectory
from simulator.simulator import Simulator, load_policy

names = ['deadline_trip_limit', 'cluster_seed_x60', 'cluster_route_x60', 'cluster_morning_route_x60']
policies = {name: load_policy('solution.policies.' + name) for name in names}
records = []
with TemporaryDirectory(prefix='is115-cluster-benchmark-') as output:
    log = Path(output) / 'log.txt'
    for name in names:  # warm-up
        Simulator('data/demand/day_001.csv', 'data/dist.csv', 'data/config.json', dispatch_policy=policies[name]).run(log)
    for repeat in range(3):
        for name in (names if repeat % 2 == 0 else list(reversed(names))):
            policy_ns = [0]; calls = [0]; call_ns = []

            def measured(parcels, context):
                start = time.perf_counter_ns()
                try:
                    return policies[name](parcels, context)
                finally:
                    elapsed = time.perf_counter_ns() - start
                    policy_ns[0] += elapsed; calls[0] += 1; call_ns.append(elapsed)

            start = time.perf_counter(); delivered = 0
            for day in range(1, 21):
                sim = Simulator(f'data/demand/day_{day:03d}.csv', 'data/dist.csv', 'data/config.json', dispatch_policy=measured)
                sim.run(log); delivered += len(sim.delivered)
            call_ns.sort()
            record = dict(policy=name, repeat=repeat + 1, total_seconds=time.perf_counter() - start,
                          policy_seconds=policy_ns[0] / 1e9, dispatch_calls=calls[0], delivered=delivered,
                          mean_call_ms=policy_ns[0] / calls[0] / 1e6,
                          p95_call_ms=call_ns[int(0.95 * (len(call_ns) - 1))] / 1e6,
                          max_call_ms=call_ns[-1] / 1e6)
            records.append(record)
            print(json.dumps(record), flush=True)
summary = []
for name in names:
    rows = [r for r in records if r['policy'] == name]
    assert len({r['delivered'] for r in rows}) == 1
    summary.append(dict(policy=name, dispatch_calls=rows[0]['dispatch_calls'], delivered=rows[0]['delivered'],
                        median_policy_seconds=statistics.median(r['policy_seconds'] for r in rows),
                        median_mean_call_ms=statistics.median(r['mean_call_ms'] for r in rows),
                        median_p95_call_ms=statistics.median(r['p95_call_ms'] for r in rows),
                        median_max_call_ms=statistics.median(r['max_call_ms'] for r in rows)))
Path('results/cluster_benchmark.json').write_text(json.dumps({'repetitions': 3, 'days_per_repetition': 20, 'records': records, 'summary': summary}, indent=2))
for s in summary:
    print(f"{s['policy']:27s} calls {s['dispatch_calls']:5d}  policy s {s['median_policy_seconds']:.3f}  mean {s['median_mean_call_ms']:.3f} ms  p95 {s['median_p95_call_ms']:.3f} ms  max {s['median_max_call_ms']:.2f} ms")
