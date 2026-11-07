# Original-data policy inventory

Each row has its module at `solution/policies/<name>.py` and 20 log/metrics pairs at `results/<name>/day_XXX/`. Run a row with `python3 run_all.py solution.policies.<name> replay_<name>`. The replay prefix preserves submitted outputs.

Supporting builder modules are shared code rather than additional independent experiments. Some variants have identical schedules.

| Variant | Delivered | Undelivered | Total penalty |
|---|---:|---:|---:|
| `baseline` | 6,421 | 9,446 | 2,702,047.24 |
| `cand_p2_A` | 15,186 | 681 | 304,815.10 |
| `cand_p2_B` | 15,187 | 680 | 292,548.30 |
| `cand_p5_A` | 15,180 | 687 | 300,687.70 |
| `cand_p5_B` | 15,183 | 684 | 288,651.61 |
| `deadline_backfill` | 15,178 | 689 | 255,240.88 |
| `deadline_cap0` | 15,207 | 660 | 308,215.69 |
| `deadline_cap15` | 15,208 | 659 | 284,770.55 |
| `deadline_cap30` | 15,208 | 659 | 271,665.53 |
| `deadline_exchange` | 14,386 | 1,481 | 527,602.03 |
| `deadline_first` | 15,206 | 661 | 355,647.04 |
| `deadline_fleet_limit` | 15,223 | 644 | 180,242.52 |
| `deadline_fleet_wait_guard` | 15,222 | 645 | 179,093.98 |
| `deadline_morning_cap` | 15,206 | 661 | 200,201.61 |
| `deadline_relocate` | 15,168 | 699 | 257,425.60 |
| `deadline_return_ties` | 15,222 | 645 | 179,078.70 |
| `deadline_size_ties` | 15,157 | 710 | 257,075.40 |
| `deadline_slack_limit` | 11,096 | 4,771 | 1,471,060.80 |
| `deadline_time_limit` | 15,222 | 645 | 179,004.33 |
| `deadline_trip_limit` | 15,222 | 645 | 179,088.70 |
| `deadline_trip_wait_guard` | 15,222 | 645 | 179,088.70 |
| `deadline_two_opt` | 15,177 | 690 | 255,466.93 |
| `deadline_window_departure` | 15,180 | 687 | 242,935.56 |
| `holdback_h120` | 15,177 | 690 | 255,466.93 |
| `holdback_h30` | 15,202 | 665 | 292,565.53 |
| `holdback_h60` | 15,179 | 688 | 260,252.25 |
| `hybrid_u0` | 15,232 | 635 | 353,473.51 |
| `hybrid_u100` | 15,206 | 661 | 355,647.04 |
| `hybrid_u100_two_opt` | 15,177 | 690 | 255,466.93 |
| `hybrid_u25` | 15,217 | 650 | 351,446.84 |
| `hybrid_u25_two_opt` | 15,166 | 701 | 296,843.07 |
| `hybrid_u50` | 15,226 | 641 | 348,157.65 |
| `hybrid_u50_two_opt` | 15,170 | 697 | 286,071.79 |
| `hybrid_u75` | 15,217 | 650 | 354,452.67 |
| `hybrid_u75_two_opt` | 15,156 | 711 | 268,031.47 |
| `nearby_first` | 15,232 | 635 | 353,473.51 |
| `nearby_local_search` | 15,175 | 692 | 328,603.53 |
| `nearby_two_opt` | 15,174 | 693 | 319,101.86 |
| `reserve_k1` | 15,136 | 731 | 229,641.92 |
| `reserve_k2` | 15,069 | 798 | 243,458.35 |
| `reserve_k3` | 15,090 | 777 | 230,509.94 |
| `reserve_k4` | 15,090 | 777 | 233,174.60 |
| `trip_limit_100` | 13,572 | 2,295 | 614,261.67 |
| `trip_limit_105` | 15,203 | 664 | 189,912.33 |
| `trip_limit_110` | 15,214 | 653 | 182,978.60 |
| `trip_limit_115` | 15,228 | 639 | 186,730.77 |
| `trip_limit_120` | 15,228 | 639 | 185,365.94 |
| `trip_limit_125` | 15,222 | 645 | 179,088.70 |
| `trip_limit_130` | 15,223 | 644 | 180,590.38 |
| `trip_limit_135` | 15,236 | 631 | 205,889.45 |
| `trip_limit_140` | 15,208 | 659 | 222,657.43 |
| `wait_f50` | 15,166 | 701 | 252,768.31 |
| `wait_f70` | 15,166 | 701 | 252,768.31 |
| `wait_f90` | 15,166 | 701 | 252,768.31 |
| `window_aware` | 15,237 | 630 | 525,915.02 |
| `window_departure_compare` | 15,170 | 697 | 245,502.42 |
| `window_departure_post2opt` | 15,177 | 690 | 255,466.93 |

The report sensitivity claim refers to the original 35-policy pool, listed explicitly in `results/report_claim_checks.json`. It excludes the later time-limit and return-tie trials and the separately reported fixed-limit sweep. Later challengers have slightly lower penalties under some weights. The selected policy is retained under the stated adoption rule, rather than claimed to be the minimum across every explored variant.

The nine `trip_limit_*` modules were created during submission recovery to reproduce already reported settings. The 100- and 140-minute logs were regenerated during this audit. Other original results were recovered from Git history or saved local experiment folders.

The modified-input stress results stay under `experiments/robustness-study-2026-11-04/`, separate from the original data and this table.
