"""Create fully specified stress inputs without editing supplied data."""
import csv
import hashlib
import json
import shutil
from pathlib import Path

import os
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

OUT=Path(__file__).resolve().parent
SCENARIOS=[
    dict(name='original',vehicles=10,shift='none'),
    dict(name='fleet_7',vehicles=7,shift='none'),
    dict(name='fleet_8',vehicles=8,shift='none'),
    dict(name='fleet_12',vehicles=12,shift='none'),
    dict(name='fleet_14',vehicles=14,shift='none'),
    dict(name='morning_arrivals_minus30',vehicles=10,shift='arrival_only',original_interval=[480,600],minutes=-30),
    dict(name='morning_arrivals_plus60',vehicles=10,shift='arrival_only',original_interval=[480,600],minutes=60),
    dict(name='all_times_plus60',vehicles=10,shift='all_times',minutes=60),
]


def minutes(value):
    h,m=map(int,value.split(':'))
    return 60*h+m


def formatted(value):
    assert 0<=value<1440,value
    return f'{value//60:02d}:{value%60:02d}'


def transform(row,scenario):
    result=dict(row)
    if scenario['shift']=='arrival_only':
        lo,hi=scenario['original_interval']
        if lo<=minutes(row['arrival_time'])<hi:
            result['arrival_time']=formatted(minutes(row['arrival_time'])+scenario['minutes'])
    elif scenario['shift']=='all_times':
        for key in ['arrival_time','delivery_window_start','delivery_window_end']:
            result[key]=formatted(minutes(row[key])+scenario['minutes'])
    return result


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    example=dict(parcel_id='P',arrival_time='08:00',delivery_window_start='10:00',delivery_window_end='11:00',size='1',delivery_location_id='A')
    early=transform(example,SCENARIOS[5]);late=transform(example,SCENARIOS[6]);whole=transform(example,SCENARIOS[7])
    assert early['arrival_time']=='07:30' and early['delivery_window_end']=='11:00'
    assert late['arrival_time']=='09:00' and late['delivery_window_start']=='10:00'
    assert whole['arrival_time']=='09:00' and whole['delivery_window_start']=='11:00' and whole['delivery_window_end']=='12:00'
    boundary=dict(example,arrival_time='10:00')
    assert transform(boundary,SCENARIOS[6])==boundary
    assert example['arrival_time']=='08:00'
    protected=[p for root in ['data','simulator','solution'] for p in Path(root).rglob('*')
               if p.is_file() and p.suffix in ['.csv','.json','.py']]
    before={str(p):digest(p) for p in protected}
    config=json.loads(Path('data/config.json').read_text())
    for scenario in SCENARIOS:
        target=OUT/'inputs'/scenario['name']
        (target/'demand').mkdir(parents=True,exist_ok=True)
        cfg={**config,'number_of_vehicles':scenario['vehicles']}
        (target/'config.json').write_text(json.dumps(cfg,indent=2)+'\n')
        shutil.copy2('data/dist.csv',target/'dist.csv')
        changed=0
        for i in range(1,21):
            day=f'day_{i:03d}'
            with Path(f'data/demand/{day}.csv').open(newline='',encoding='utf-8-sig') as f:
                reader=csv.DictReader(f);fields=reader.fieldnames;original=list(reader)
            transformed=[transform(row,scenario) for row in original]
            assert len(transformed)==len(original)
            assert {r['parcel_id'] for r in transformed}=={r['parcel_id'] for r in original}
            for a,b in zip(original,transformed):
                for field in ['parcel_id','size','delivery_location_id']:assert a[field]==b[field]
                changed+=a!=b
                assert minutes(b['delivery_window_start'])<=minutes(b['delivery_window_end'])
            with (target/'demand'/f'{day}.csv').open('w',newline='',encoding='utf-8') as f:
                writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(transformed)
        scenario['changed_parcel_records']=changed
    assert before=={str(p):digest(p) for p in protected}
    (OUT/'protected_hashes.json').write_text(json.dumps(before,indent=2)+'\n')
    plan=dict(scenarios=SCENARIOS,
              policies=['deadline_trip_limit','deadline_time_limit','deadline_return_ties','fixed_120','deadline_window_departure'],
              operating_hours='Planning 08:00-17:30 and return by 18:00 unchanged in every scenario.',
              transformations='Morning interval is based on ORIGINAL arrival, 08:00 inclusive to 10:00 exclusive; shift arrival only, keep windows unchanged. No clipping or wrapping. All-times shift moves arrival and both windows by 60 min.',
              comparison='Use the same penalty in each scenario; report gaps to the best of these five candidates. Average/worst scenario gaps weight eight scenarios equally.',
              limitation='Independent precisely defined scenarios, not claimed identical to Chloe\'s unspecified time shifts. Same underlying 20 development days; no new independent test set.',
              previous_gate='This newly authorised robustness study includes marginal challengers that failed the previous adoption threshold. Their original-data results and that decision remain unchanged.')
    (OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(plan,indent=2))


if __name__=='__main__':main()
