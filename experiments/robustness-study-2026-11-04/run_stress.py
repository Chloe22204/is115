"""Run selected predeclared scenarios. Run from GitHub with PYTHONPATH=."""
import collections
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import os
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import check_trips
from simulator.simulator import Simulator, load_policy
from solution.performance_monitor import calculate_metrics
from solution.policies.deadline_window_departure import dispatch as window_dispatch

OUT=Path(__file__).resolve().parent
PLAN=json.loads((OUT/'plan.json').read_text())
NAMES=PLAN['policies']


def rows(path):
    with Path(path).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))


def fixed_120(parcels,context):
    departure=context['current_time']+context['departure_delay']
    limited={**context,'return_cutoff':min(context['return_cutoff'],departure+120.0)}
    return window_dispatch(parcels,limited)


def limit_for(name,now):
    if name=='deadline_window_departure':return 320.0
    if name=='fixed_120':return 120.0
    if name=='deadline_time_limit' and now<600:return 110.0
    return 125.0


def verify_original(name,day,log):
    sources={
        'deadline_trip_limit':Path('results/deadline_trip_limit'),
        'deadline_window_departure':Path('results/deadline_window_departure'),
        'fixed_120':OUT.parent/'trip-limit-validation-2026-11-04/results/cap_120',
        'deadline_time_limit':OUT.parent/'time-limit-experiment-2026-11-04/results/deadline_time_limit',
        'deadline_return_ties':OUT.parent/'return-tie-experiment-2026-11-04/results/deadline_return_ties'}
    assert log.read_bytes()==(sources[name]/day/'log.txt').read_bytes(),(name,day,'original replay differs')


def main():
    requested=sys.argv[1:]
    assert requested,'Pass scenario names from plan.json'
    scenarios={s['name']:s for s in PLAN['scenarios']}
    assert all(name in scenarios for name in requested)
    policies={name:(fixed_120 if name=='fixed_120' else load_policy('solution.policies.'+name)) for name in NAMES}
    protected=json.loads((OUT/'protected_hashes.json').read_text())
    for scenario in requested:
        data=OUT/'inputs'/scenario
        result_root=OUT/'results'/scenario
        check_trips.RESULTS=result_root
        config=json.loads((data/'config.json').read_text())
        distrows=rows(data/'dist.csv')
        distances={}
        for r in distrows:distances.setdefault(r['location_1'],{})[r['location_2']]=float(r['dist'])
        daily={name:[] for name in NAMES}
        for i in range(1,21):
            day=f'day_{i:03d}'
            demand_rows=rows(data/'demand'/f'{day}.csv')
            demand={p['parcel_id']:p for p in demand_rows}
            for name in NAMES:
                traces={};ids=collections.Counter();calls=0

                def measured(parcels,context):
                    nonlocal calls
                    calls+=1
                    now=context['current_time'];departure=now+context['departure_delay']
                    selected=policies[name](parcels,context)
                    assert len(selected)==len(set(selected))
                    for pid in selected:
                        p=parcels[pid]
                        assert p['arrival_time']<=now and p['vehicle_assigned'] is None and p['delivery_time'] is None
                    if selected:
                        assert math.fsum(parcels[p]['size'] for p in selected)<=context['capacity']+1e-9
                        places=['HUB']+[parcels[p]['delivery_location_id'] for p in selected]+['HUB']
                        duration=math.fsum(distances[a][b] for a,b in zip(places,places[1:]))
                        assert duration<=limit_for(name,now)+1e-8
                        assert duration<=context['max_trip_distance_km']+1e-8
                        assert departure+duration<=context['return_cutoff']+1e-8
                        v=context['vehicle_id'];ids[v]+=1
                        traces[v,ids[v]]=dict(planning=now,departure=departure,duration=duration,route=list(selected))
                    return selected

                output=result_root/name/day
                output.mkdir(parents=True,exist_ok=True)
                log=output/'log.txt'
                sim=Simulator(data/'demand'/f'{day}.csv',data/'dist.csv',data/'config.json',dispatch_policy=measured)
                sim.run(log)
                if scenario=='original':verify_original(name,day,log)
                events=[json.loads(line) for line in log.read_text().splitlines() if line.strip()]
                metrics=calculate_metrics(demand_rows,distrows,config,events)
                (output/'metrics.json').write_text(json.dumps(metrics,indent=2,allow_nan=False)+'\n')
                trips,violations=check_trips.check_day(name,day,demand,distances,config)
                assert not violations,violations
                assert trips==len(traces)
                departures={(e['vehicle_id'],e['trip_id']):e['time'] for e in events if e['event_type']=='hub_departure'}
                deliveries=collections.defaultdict(list)
                returns=collections.defaultdict(list)
                for e in events:
                    if e['event_type']=='delivery':deliveries[e['vehicle_id'],e['trip_id']].append((e['parcel_id'],e['time']))
                    elif e['event_type']=='vehicle_return' and e['time']!=480:returns[e['vehicle_id']].append(e['time'])
                seen=set();expected_returns=collections.defaultdict(list)
                for key,trace in sorted(traces.items()):
                    assert abs(departures[key]-trace['departure'])<1e-7
                    assert [pid for pid,_ in deliveries[key]]==trace['route']
                    at=trace['departure'];origin='HUB'
                    for pid,actual in deliveries[key]:
                        assert pid not in seen
                        seen.add(pid)
                        dest=demand[pid]['delivery_location_id']
                        at+=distances[origin][dest]
                        assert abs(at-actual)<1e-7
                        origin=dest
                    ret=at+distances[origin]['HUB']
                    if expected_returns[key[0]]:assert trace['planning']+1e-7>=expected_returns[key[0]][-1]
                    expected_returns[key[0]].append(ret)
                for v,times in expected_returns.items():
                    assert len(times)==len(returns[v])
                    assert all(abs(a-b)<1e-7 for a,b in zip(times,returns[v]))
                row=dict(day=day,**{k:v for k,v in metrics.items() if k!='trips'},
                         driving_km=round(math.fsum(t['duration'] for t in traces.values()),6),dispatch_calls=calls)
                daily[name].append(row)
            if i in [5,10,15,20]:print(scenario,day,'completed',flush=True)
        fields=['total_penalty','undelivered_parcels','delivered_parcels','total_early_minutes','total_late_minutes','number_of_trips','driving_km','dispatch_calls']
        totals={name:{k:round(sum(r[k] for r in daily[name]),3 if k=='driving_km' else 2) for k in fields} for name in NAMES}
        for name in NAMES:
            totals[name]['first10']=round(sum(r['total_penalty'] for r in daily[name][:10]),2)
            totals[name]['last10']=round(sum(r['total_penalty'] for r in daily[name][10:]),2)
        result=dict(scenario=scenarios[scenario],policies=NAMES,totals=totals,daily=daily,
                    runs=100,trips_checked=sum(t['number_of_trips'] for t in totals.values()),violations=0)
        (OUT/f'{scenario}_summary.json').write_text(json.dumps(result,indent=2)+'\n')
        print('SUMMARY',scenario,{name:totals[name]['total_penalty'] for name in NAMES},flush=True)
    for path,expected in protected.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected,path
    print('All requested scenarios complete; protected inputs and source hashes unchanged.',flush=True)


if __name__=='__main__':main()
