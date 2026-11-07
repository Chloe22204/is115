# Trip-limit evidence

The selected policy remains `deadline_trip_limit`. Its score over the supplied 20 days is 179,088.70, with 645 undelivered parcels, 447.91 early minutes and 23,840.78 late minutes. It improves on `deadline_window_departure` by 26.3%.

All nine limits reported in Section 5.5 have a standalone module (`solution/policies/trip_limit_<minutes>.py`) and 20 daily log/metrics pairs (`results/trip_limit_<minutes>/day_XXX/`). Their totals are:

| Limit | Penalty |
|---|---:|
| 100 | 614,261.67 |
| 105 | 189,912.33 |
| 110 | 182,978.60 |
| 115 | 186,730.77 |
| 120 | 185,365.94 |
| 125 | 179,088.70 |
| 130 | 180,590.38 |
| 135 | 205,889.45 |
| 140 | 222,657.43 |

The 100- and 140-minute logs were regenerated on 5 November to verify the existing report claims. They are not claimed to be original retained logs. The other seven settings were recovered and verified from saved evidence. All policy wrapper modules were added during recovery to make each setting runnable separately.

The seven-setting sweep and split-half calculations are preserved in `../experiments/trip-limit-validation-2026-11-04/`. The reported range 105–130 is within 6.044% of the best, so “within 6.1%” is accurate. All 20 days informed development.

The reproducible later stress study is in `../experiments/robustness-study-2026-11-04/`. It compares five candidates over eight explicitly defined scenarios. Fixed 125 has a mean gap of 2.1254% and a worst gap of 6.0342%, and wins no scenario outright. No candidate wins every scenario.

The earlier four-candidate stress summary has not been independently reproduced. Its precise scenario generator and results remain unavailable. It must not be merged with the later reproducible five-candidate study.

See `reproduction.md` for commands.
