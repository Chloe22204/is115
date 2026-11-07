import json,statistics,time
from pathlib import Path
from tempfile import TemporaryDirectory
from simulator.simulator import Simulator,load_policy

names=['baseline','deadline_first','nearby_first','window_aware','nearby_local_search','nearby_two_opt']
policies={name:load_policy('solution.policies.'+name) for name in names}
records=[]
with TemporaryDirectory(prefix='is115-benchmark-') as output:
 log=Path(output)/'log.txt'
 # Warm up imports and the input-reading path before measured runs.
 for name in names:
  sim=Simulator('data/demand/day_001.csv','data/dist.csv','data/config.json',dispatch_policy=policies[name])
  sim.run(log)
 for repeat in range(3):
  order=names if repeat%2==0 else list(reversed(names))
  for name in order:
   policy_ns=[0];calls=[0]
   def measured(parcels,context):
    start=time.perf_counter_ns()
    try:return policies[name](parcels,context)
    finally:
     policy_ns[0]+=time.perf_counter_ns()-start;calls[0]+=1
   start=time.perf_counter()
   delivered=0
   for day in range(1,21):
    sim=Simulator(f'data/demand/day_{day:03d}.csv','data/dist.csv','data/config.json',dispatch_policy=measured)
    sim.run(log);delivered+=len(sim.delivered)
   total=time.perf_counter()-start
   record=dict(policy=name,repeat=repeat+1,total_seconds=total,policy_seconds=policy_ns[0]/1e9,dispatch_calls=calls[0],delivered=delivered)
   records.append(record)
   print(json.dumps(record),flush=True)
summary=[]
for name in names:
 rows=[r for r in records if r['policy']==name]
 assert len({r['delivered'] for r in rows})==1
 summary.append(dict(policy=name,median_total_seconds=statistics.median(r['total_seconds'] for r in rows),min_total_seconds=min(r['total_seconds'] for r in rows),max_total_seconds=max(r['total_seconds'] for r in rows),median_policy_seconds=statistics.median(r['policy_seconds'] for r in rows),dispatch_calls=rows[0]['dispatch_calls'],delivered=rows[0]['delivered']))
Path('results/benchmark.json').write_text(json.dumps({'repetitions':3,'days_per_repetition':20,'records':records,'summary':summary},indent=2))
print('SUMMARY',json.dumps(summary),flush=True)
