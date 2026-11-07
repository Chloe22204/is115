"""Independently reproduce the reported seven-value trip-limit sweep.

Run from GitHub with PYTHONPATH=.; writes only beside this script.
This validates previously reported settings, not a new search for parameters.
"""
import collections
import csv
import hashlib
import json
import math
from pathlib import Path

import os
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import check_trips
from simulator.simulator import Simulator
from solution.performance_monitor import calculate_metrics
from solution.policies.deadline_window_departure import dispatch as window_dispatch

OUT = Path(__file__).resolve().parent
RESULTS = OUT / 'results'
LIMITS = [105, 110, 115, 120, 125, 130, 135]
REPORTED_TOTALS = {105:189912,110:182979,115:186731,120:185366,125:179089,130:180590,135:205889}


def rows(path):
    with Path(path).open(newline='', encoding='utf-8-sig') as stream:
        return list(csv.DictReader(stream))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    config=json.loads(Path('data/config.json').read_text())
    distances_rows=rows('data/dist.csv')
    distances=check_trips.load_distances()
    check_trips.RESULTS=RESULTS
    protected=[p for root in ['data','simulator','solution'] for p in Path(root).rglob('*')
               if p.is_file() and (p.suffix in ['.csv','.json','.py'])]
    before={str(p):digest(p) for p in protected}
    summary=[]
    total_trips=0
    for limit in LIMITS:
        name=f'cap_{limit}'
        daily=[]
        for i in range(1,21):
            day=f'day_{i:03d}'
            traces=[]

            def policy(parcels,context):
                now=context['current_time']
                departure=now+context['departure_delay']
                limited={**context,'return_cutoff':min(context['return_cutoff'],departure+limit)}
                selected=window_dispatch(parcels,limited)
                assert len(selected)==len(set(selected))
                for pid in selected:
                    p=parcels[pid]
                    assert p['arrival_time']<=now and p['vehicle_assigned'] is None and p['delivery_time'] is None
                if selected:
                    locations=['HUB']+[parcels[pid]['delivery_location_id'] for pid in selected]+['HUB']
                    duration=math.fsum(distances[a][b] for a,b in zip(locations,locations[1:]))
                    assert duration<=limit+1e-8
                    assert departure+duration<=1080+1e-8
                    traces.append(duration)
                return selected

            output=RESULTS/name/day
            output.mkdir(parents=True,exist_ok=True)
            log=output/'log.txt'
            sim=Simulator(f'data/demand/{day}.csv','data/dist.csv','data/config.json',dispatch_policy=policy)
            sim.run(log)
            if limit==125:
                assert log.read_bytes()==Path(f'results/deadline_trip_limit/{day}/log.txt').read_bytes(),day
            demand=rows(f'data/demand/{day}.csv')
            events=[json.loads(line) for line in log.read_text().splitlines() if line.strip()]
            metrics=calculate_metrics(demand,distances_rows,config,events)
            (output/'metrics.json').write_text(json.dumps(metrics,indent=2,allow_nan=False)+'\n')
            trips,violations=check_trips.check_day(name,day,{p['parcel_id']:p for p in demand},distances,config)
            assert not violations,violations
            assert trips==len(traces)
            total_trips+=trips
            daily.append(dict(day=day,**{k:v for k,v in metrics.items() if k!='trips'}))
        row=dict(limit=limit,first10=round(sum(r['total_penalty'] for r in daily[:10]),2),
                 last10=round(sum(r['total_penalty'] for r in daily[10:]),2),
                 total=round(sum(r['total_penalty'] for r in daily),2),
                 undelivered=sum(r['undelivered_parcels'] for r in daily),daily=daily)
        row['reported_total']=REPORTED_TOTALS[limit]
        row['matches_reported_rounding']=abs(row['total']-row['reported_total'])<=1.0
        assert row['matches_reported_rounding'],(limit,row['total'])
        summary.append(row)
        print({k:v for k,v in row.items() if k!='daily'},flush=True)
    assert before=={str(p):digest(p) for p in protected}
    best=min(summary,key=lambda r:r['total'])
    for r in summary:r['gap_to_best_pct']=round(100*(r['total']/best['total']-1),4)
    first_choice=min(summary,key=lambda r:r['first10'])
    second_choice=min(summary,key=lambda r:r['last10'])
    old_first=sum(json.loads(Path(f'results/deadline_window_departure/day_{i:03d}/metrics.json').read_text())['total_penalty'] for i in range(1,11))
    old_second=sum(json.loads(Path(f'results/deadline_window_departure/day_{i:03d}/metrics.json').read_text())['total_penalty'] for i in range(11,21))
    checks=dict(best_all20=best['limit'],choose_on_first10=first_choice['limit'],
                other_half_improvement_pct=round(100*(old_second-first_choice['last10'])/old_second,4),
                choose_on_last10=second_choice['limit'],
                first_half_improvement_pct=round(100*(old_first-second_choice['first10'])/old_first,4),
                max_105_to_130_gap_pct=max(r['gap_to_best_pct'] for r in summary if r['limit']<=130))
    result=dict(limits=LIMITS,summary=summary,split_checks=checks,trips_checked=total_trips,
                validation='140 runs; active caps, original hard constraints, unique/eligible selection checked; all 20 cap125 logs match saved logs exactly; protected source/input files unchanged.',
                limitation='All 20 days informed development. Split selection is a retrospective robustness check, not untouched evaluation. Modified-data stress claims have not been reproduced by this script.')
    (OUT/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(checks,indent=2),flush=True)
    print(result['validation'],flush=True)


if __name__=='__main__':
    main()
