# Anchor-based geography experiment

This experiment tests whether grouping parcels near an urgent first stop improves
the locked `deadline_trip_limit` policy. It does not change the submission.

The reference is commit `2539477`. The trip cap stays at 125 minutes, with the
same waiting rule, 2-opt, capacity, range and scoring weights. The policy uses
only the parcel and context snapshots. Distances come from the supplied directed
table; no coordinates or future arrivals are assumed.

## Selection rule

Choose the earliest-deadline feasible parcel as the first stop. For each later
addition, find the earliest deadline among the remaining feasible parcels.
Consider parcels within 0, 30 or 60 minutes of that deadline, then rank them by
distance from the first stop, current-leg distance, deadline and parcel ID.
The existing waiting check runs on the constructed route, before 2-opt.

The three bands and adoption rule were recorded in `plan.json` before running.
Days 1–10 choose the candidate; days 11–20 compare it with the reference.
All these days were used before, so this is not an unseen test.

## Results

| Metric across 20 days | Locked policy | Anchor grouping |
|---|---:|---:|
| Total penalty | 179,088.70 | 200,644.45 |
| Delivered | 15,222 | 15,226 |
| Undelivered | 645 | 641 |
| Early minutes | 447.91 | 21,880.44 |
| Late minutes | 23,840.78 | 24,924.00 |
| Late minutes for parcels arriving 08:00–10:00 | 18,031.269 | 18,878.134 |
| Driving distance in km | 73,341.609 | 77,251.170 |
| Trips | 817 | 822 |
| Days beating the locked policy | — | 1 of 20 |

Penalty increases by 12.04%. Four extra deliveries save 960 points, but the
additional early and late minutes outweigh that saving. Travel also increases
by 5.33%, so this rule does not achieve the hoped-for travel reduction.
Higher earliness is observed; this experiment does not separately identify how
much comes from parcel selection, the waiting decision or subsequent 2-opt.

All three settings produced byte-identical logs and metrics on all 20 days.
They are one effective outcome on these inputs, not three independent results.
A replay of all 1,838 construction calls for the zero-band policy confirmed that
using bands 30 or 60 did not change any constructed route. The small synthetic
tests confirm that the band can change selection on other inputs.

The first-half tie selected band 0 before evaluating the second half. Its
days 1–10 penalty was 96,716.05 against 90,383.74. Its days 11–20 penalty was
103,928.40 against 88,704.96, which is 17.16% worse. It fails the adoption rule.

## Validation and reproduction

Run from the experiment checkout:

```bash
python3 experiments/geography-selection-2026-11-12/test_geography.py
python3 experiments/geography-selection-2026-11-12/run_experiment.py
```

Rerunning replaces only this experiment's result files. It leaves the original
saved results intact. Each policy-day has its `log.txt` and `metrics.json` under
`results/<policy>/day_XXX/` beside this document.

All 80 runs completed with zero violations across 3,283 trips. Every dispatch
was checked for input mutation, duplicate or unavailable parcels, capacity,
range, the 125-minute limit and the return cutoff. Independent event-log checks
also passed. All 20 control logs and metrics matched the original saved files
byte-for-byte. The six small tests pass on Python 3.9.6 and 3.13.7.

`summary.json` contains the daily metrics, aggregate results, source hashes and
single-run dispatch timings. Those timings are descriptive, not a repeated
benchmark. `selection.json` records the first-half choice, and
`band_diagnostic.json` records the construction comparison.

Keep the locked policy. This result rejects this particular anchor-first rule;
it does not prove that every geographic grouping method would fail.
