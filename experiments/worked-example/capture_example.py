"""Replay the selected policy and record a short real 2-opt example."""
import hashlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))
from simulator.simulator import Simulator
from simulator.loaders import day_input_paths
from solution.policies.deadline_trip_limit import dispatch
from solution.policies.deadline_first import dispatch as greedy
from solution.policies.helpers import route_timing_penalty

def describe(route, parcels, context):
    now = context['current_time'] + context['departure_delay']
    departure = now
    location = 'HUB'
    stops = []
    for pid in route:
        p = parcels[pid]
        now += context['travel_distance'][location][p['delivery_location_id']]
        early = max(0.0, p['delivery_window_start'] - now)
        late = max(0.0, now - p['delivery_window_end'])
        stops.append(dict(parcel_id=pid, destination=p['delivery_location_id'],
                          size=p['size'], window_start=p['delivery_window_start'],
                          window_end=p['delivery_window_end'], arrival=now,
                          early=early, late=late))
        location = p['delivery_location_id']
    returned = now + context['travel_distance'][location]['HUB']
    return dict(order=route, stops=stops, departure=departure, returned=returned,
                duration=returned-departure, load=math.fsum(parcels[p]['size'] for p in route),
                early=math.fsum(s['early'] for s in stops),
                late=math.fsum(s['late'] for s in stops),
                penalty=route_timing_penalty(route, parcels, context))

cases = []
matches = []
for number in range(1, 21):
    day = f'day_{number:03d}'
    def observed(parcels, context):
        chosen = dispatch(parcels, context)
        if len(chosen) >= 2:
            departure = context['current_time'] + context['departure_delay']
            limited = dict(context, return_cutoff=min(context['return_cutoff'], departure+125))
            initial = greedy(parcels, limited)
            if chosen != initial:
                before = describe(initial, parcels, limited)
                after = describe(chosen, parcels, limited)
                if before['penalty'] - after['penalty'] > 0.1:
                    assert set(initial) == set(chosen)
                    cases.append(dict(day=day, vehicle_id=context['vehicle_id'],
                                      planning_time=context['current_time'], before=before, after=after))
        return chosen
    log = HERE / 'replay' / day / 'log.txt'
    sim = Simulator(*day_input_paths(REPO / 'data', day), dispatch_policy=observed)
    sim.run(log)
    match = log.read_bytes() == (REPO/'results'/'deadline_trip_limit'/day/'log.txt').read_bytes()
    assert match, day
    matches.append(match)

assert cases, 'No short improving case found'
cases.sort(key=lambda c: (len(c['after']['order']), -(c['before']['penalty']-c['after']['penalty'])))
selected = cases[0]
events = [json.loads(line) for line in (HERE/'replay'/selected['day']/'log.txt').read_text().splitlines()]
departures = [e for e in events if e['event_type']=='hub_departure' and e['vehicle_id']==selected['vehicle_id'] and e['time']==selected['after']['departure']]
assert len(departures)==1
selected['trip_id'] = departures[0]['trip_id']
deliveries = [e for e in events if e['event_type']=='delivery' and e['vehicle_id']==selected['vehicle_id'] and e['trip_id']==selected['trip_id']]
assert [e['parcel_id'] for e in deliveries] == selected['after']['order']
assert all(abs(e['time']-s['arrival'])<1e-8 for e,s in zip(deliveries,selected['after']['stops']))
for route in ['before','after']:
    assert selected[route]['load'] <= 30+1e-9
    assert selected[route]['duration'] <=125+1e-9
    assert selected[route]['returned'] <=1080
selected['verification'] = dict(exact_replay_days=sum(matches), candidates_found=len(cases),
    delivered_order_and_times_match_log=True,
    same_selected_parcels=True,
    input_sha256=hashlib.sha256((REPO/'data'/'demand'/(selected['day']+'.csv')).read_bytes()).hexdigest())
(HERE/'selected_example.json').write_text(json.dumps(selected,indent=2)+'\n')
print(json.dumps(selected,indent=2))
