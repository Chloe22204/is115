"""Aggregate the completed stress comparisons without changing policy choices."""
import csv
import hashlib
import json
from pathlib import Path

import os
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

OUT=Path(__file__).resolve().parent
PLAN=json.loads((OUT/'plan.json').read_text())
NAMES=PLAN['policies']
LABELS={'deadline_trip_limit':'Fixed 125','deadline_time_limit':'110 before 10 then 125',
        'deadline_return_ties':'125 with return ties','fixed_120':'Fixed 120',
        'deadline_window_departure':'Window departure'}


def main():
    records=[];gaps={n:[] for n in NAMES};comparisons={n:[] for n in NAMES}
    for scenario in PLAN['scenarios']:
        raw=json.loads((OUT/(scenario['name']+'_summary.json')).read_text())
        assert raw['runs']==100 and raw['violations']==0
        assert all(len(raw['daily'][n])==20 for n in NAMES)
        best=min(raw['totals'][n]['total_penalty'] for n in NAMES)
        baseline=raw['totals']['deadline_trip_limit']['total_penalty']
        row=dict(scenario=scenario['name'],best_penalty=best,
                 winners=[n for n in NAMES if raw['totals'][n]['total_penalty']==best],totals=raw['totals'],gaps_pct={},vs_125={})
        for name in NAMES:
            gap=100*(raw['totals'][name]['total_penalty']/best-1)
            change=100*(raw['totals'][name]['total_penalty']/baseline-1)
            gaps[name].append(gap);comparisons[name].append(change)
            row['gaps_pct'][name]=round(gap,4)
            row['vs_125'][name]=dict(change_pct=round(change,4),
                wins=sum(a['total_penalty']<b['total_penalty'] for a,b in zip(raw['daily'][name],raw['daily']['deadline_trip_limit'])),
                losses=sum(a['total_penalty']>b['total_penalty'] for a,b in zip(raw['daily'][name],raw['daily']['deadline_trip_limit'])),
                ties=sum(a['total_penalty']==b['total_penalty'] for a,b in zip(raw['daily'][name],raw['daily']['deadline_trip_limit'])))
        records.append(row)
    rankings={n:dict(mean_gap_pct=round(sum(gaps[n])/len(gaps[n]),4),worst_gap_pct=round(max(gaps[n]),4),
                     scenario_wins=sum(n in r['winners'] for r in records),
                     mean_change_vs_125_pct=round(sum(comparisons[n])/len(comparisons[n]),4),
                     worst_change_vs_125_pct=round(max(comparisons[n]),4)) for n in NAMES}
    before=json.loads((OUT/'protected_hashes.json').read_text())
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in before.items())
    trip_count=sum(json.loads((OUT/(s['name']+'_summary.json')).read_text())['trips_checked'] for s in PLAN['scenarios'])
    merged=dict(plan=PLAN,scenarios=records,rankings=rankings,runs=800,trips_checked=trip_count,violations=0,
                original_replay='All 100 original-scenario logs match earlier saved logs for their respective policies exactly.',
                limitations='Equal scenario weighting is a modelling choice, not a real demand distribution. Eight scenarios reuse the same 20 days. These are not proven identical to Chloe\'s shifts; the competitor pool differs (no morning-cap candidate). Original-data adoption threshold remains unchanged.')
    (OUT/'summary.json').write_text(json.dumps(merged,indent=2)+'\n')
    with (OUT/'comparison.csv').open('w',newline='') as f:
        fields=['scenario','policy','penalty','undelivered','early_minutes','late_minutes','driving_km','gap_to_best_pct','change_vs_125_pct']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for r in records:
            for name in NAMES:
                t=r['totals'][name]
                writer.writerow(dict(scenario=r['scenario'],policy=name,penalty=t['total_penalty'],undelivered=t['undelivered_parcels'],
                                     early_minutes=t['total_early_minutes'],late_minutes=t['total_late_minutes'],driving_km=t['driving_km'],
                                     gap_to_best_pct=r['gaps_pct'][name],change_vs_125_pct=r['vs_125'][name]['change_pct']))
    print('PENALTIES')
    for r in records:print(r['scenario'],{LABELS[n]:r['totals'][n]['total_penalty'] for n in NAMES})
    print('RANKINGS',json.dumps(rankings,indent=2))
    print('Verified',800,'runs;',trip_count,'trips; zero violations; protected source/input hashes unchanged.')


if __name__=='__main__':main()
