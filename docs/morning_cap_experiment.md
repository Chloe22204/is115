# Follow-up: capping morning trip length

Reference: `deadline_window_departure` (branch `codex/return-time-caps`, commit `3812151`).

## Diagnosis

- 561 of the reference's 687 undelivered parcels arrive too late for any van to
  return by 18:00 (matches `analyze_floor.py`). No policy can recover them.
- All 76,184 late minutes are avoidable in isolation. 62k come from two daily
  groups: arrivals 08:xx due 10:xx, and arrivals 09:xx due 10:00-11:00.
- By about 09:30 all 10 vans have left on ~3-hour trips; the first returns
  around 10:20, so these parcels go out on second trips at 11:00-12:00.

## Rule

`deadline_morning_cap`: trips planned before 10:00 must return by 10:15.
Otherwise identical to `deadline_window_departure`. Code: `solution/policies/morning_rush.py`.

## Results (20 days)

| Policy | Penalty | Undelivered | Early min | Late min | Days better/worse |
|---|---:|---:|---:|---:|---|
| deadline_window_departure | 242,935.56 | 687 | 1,871.91 | 76,183.63 | - |
| deadline_morning_cap | 200,202 | 661 | 1,117 | 40,444 | 18 / 2 |

Days 1-10: -12.1%; days 11-20: -22.5%. Passes the adoption rule.

## Sensitivity sweep (before = planning cutoff, r = latest return, minutes after midnight)

Planning cutoffs 09:30-10:00 with returns 10:00-10:30 all score -16% to -18%.
Returns after about 10:45 hurt (11:00: +11%, 11:30: +85%). Reserving 1-4 idle
vans until 10:00 instead (`reserve_k1`-`reserve_k4`) reduced lateness but raised
undelivered parcels to 731-798, scoring -5.5% to +0.2%.

Parameters were chosen on the same 20 days they are scored on; there is no
untouched evaluation set.

```
deadline_window_departure  pen=    242936 (+0.0%) undel= 687 early=   1872 late=  76184 d1-10 +0.0% d11-20 +0.0% W/L=0/0
_sw_b570_r570              pen=    244392 (+0.6%) undel= 775 early=  11705 late=  46687 d1-10 -0.1% d11-20 +1.2% W/L=11/9
_sw_b570_r585              pen=    222361 (-8.5%) undel= 732 early=   8586 late=  38094 d1-10 -2.7% d11-20 -13.6% W/L=13/7
_sw_b570_r600              pen=    207945 (-14.4%) undel= 702 early=   3122 late=  36344 d1-10 -3.2% d11-20 -24.4% W/L=16/4
_sw_b570_r615              pen=    199760 (-17.8%) undel= 662 early=   1107 late=  39772 d1-10 -12.2% d11-20 -22.8% W/L=18/2
_sw_b570_r630              pen=    203419 (-16.3%) undel= 634 early=   1153 late=  50106 d1-10 -10.7% d11-20 -21.2% W/L=16/4
_sw_b570_r645              pen=    219489 (-9.7%) undel= 625 early=   3077 late=  66412 d1-10 -5.6% d11-20 -13.3% W/L=13/7
_sw_b600_r600              pen=    198904 (-18.1%) undel= 664 early=   1057 late=  38487 d1-10 -12.1% d11-20 -23.5% W/L=16/4
_sw_b600_r615              pen=    200202 (-17.6%) undel= 661 early=   1117 late=  40444 d1-10 -12.1% d11-20 -22.5% W/L=18/2
_sw_b600_r630              pen=    204090 (-16.0%) undel= 633 early=   1153 late=  51018 d1-10 -10.4% d11-20 -21.0% W/L=16/4
_sw_b600_r645              pen=    219489 (-9.7%) undel= 625 early=   3077 late=  66412 d1-10 -5.6% d11-20 -13.3% W/L=13/7
_sw_b630_r630              pen=    229903 (-5.4%) undel= 626 early=    633 late=  79031 d1-10 -1.7% d11-20 -8.7% W/L=11/9
_sw_b630_r645              pen=    234315 (-3.5%) undel= 627 early=   2621 late=  81214 d1-10 -1.2% d11-20 -5.7% W/L=9/11
morning_cap_660            pen=    270367 (+11.3%) undel= 650 early=  11250 late= 103117 d1-10 +15.1% d11-20 +7.9% W/L=5/15
morning_cap_690            pen=    448967 (+84.8%) undel= 782 early=  18790 late= 242496 d1-10 +95.1% d11-20 +75.6% W/L=0/20
reserve_k1                 pen=    229642 (-5.5%) undel= 731 early=   3143 late=  51059 d1-10 +1.6% d11-20 -11.7% W/L=13/7
reserve_k2                 pen=    243458 (+0.2%) undel= 798 early=   6875 late=  45063 d1-10 +8.3% d11-20 -7.0% W/L=11/9
reserve_k3                 pen=    230510 (-5.1%) undel= 777 early=   6107 late=  37923 d1-10 +5.8% d11-20 -14.8% W/L=11/9
reserve_k4                 pen=    233175 (-4.0%) undel= 777 early=   5849 late=  40846 d1-10 +11.3% d11-20 -17.7% W/L=12/8
```
