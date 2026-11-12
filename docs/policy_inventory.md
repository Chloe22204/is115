# Original-data policy inventory

Each row has its module at `solution/policies/<name>.py` and 20 log/metrics pairs at `results/<name>/day_XXX/`. Run a row with `python3 run_all.py solution.policies.<name> replay_<name>`. The replay prefix preserves submitted outputs.

Supporting builder modules are shared code rather than additional independent experiments. Some variants have identical schedules.

## Counts

`results/` holds **64 original-data variants**, each with 20 day folders (1,280 policy-days). All 64 are listed below.

- **9 main comparison policies**, reported in the main comparison of `report.pdf`: `baseline`, `deadline_first`, `nearby_first`, `window_aware`, `nearby_local_search`, `nearby_two_opt`, `deadline_two_opt`, `deadline_window_departure` and `deadline_trip_limit` (selected).
- **55 supplementary variants**: urgency hybrids, candidate selection, hold-back, wait-to-fill, reserve, morning cap, exchange/relocate/backfill, fleet, slack and time limits, tie-break and return-cap trials, window-departure comparisons, the `trip_limit_*` sweep, and the seven `cluster_*` seed-and-cluster variants (see [cluster_experiment.md](cluster_experiment.md); none adopted).

Pool sizes used elsewhere: the report sensitivity claim uses the original 35-policy pool, and `results/report_claim_checks.json` records an expanded pool of 57 variants. Both were defined before the seven `cluster_*` variants were added, which brings the total to 64.

| Variant | Group | Delivered | Undelivered | Total penalty |
|---|---|---:|---:|---:|
| `baseline` | Main | 6,421 | 9,446 | 2,702,047.24 |
| `cand_p2_A` | Supplementary | 15,186 | 681 | 304,815.10 |
| `cand_p2_B` | Supplementary | 15,187 | 680 | 292,548.30 |
| `cand_p5_A` | Supplementary | 15,180 | 687 | 300,687.70 |
| `cand_p5_B` | Supplementary | 15,183 | 684 | 288,651.61 |
| `cluster_morning_route_x60` | Supplementary | 15,225 | 642 | 178,033.69 |
| `cluster_route_x120` | Supplementary | 15,218 | 649 | 179,987.27 |
| `cluster_route_x240` | Supplementary | 15,222 | 645 | 181,172.79 |
| `cluster_route_x60` | Supplementary | 15,218 | 649 | 179,987.27 |
| `cluster_seed_x120` | Supplementary | 15,190 | 677 | 188,011.80 |
| `cluster_seed_x240` | Supplementary | 15,204 | 663 | 188,411.91 |
| `cluster_seed_x60` | Supplementary | 15,190 | 677 | 188,011.80 |
| `deadline_backfill` | Supplementary | 15,178 | 689 | 255,240.88 |
| `deadline_cap0` | Supplementary | 15,207 | 660 | 308,215.69 |
| `deadline_cap15` | Supplementary | 15,208 | 659 | 284,770.55 |
| `deadline_cap30` | Supplementary | 15,208 | 659 | 271,665.53 |
| `deadline_exchange` | Supplementary | 14,386 | 1,481 | 527,602.03 |
| `deadline_first` | Main | 15,206 | 661 | 355,647.04 |
| `deadline_fleet_limit` | Supplementary | 15,223 | 644 | 180,242.52 |
| `deadline_fleet_wait_guard` | Supplementary | 15,222 | 645 | 179,093.98 |
| `deadline_morning_cap` | Supplementary | 15,206 | 661 | 200,201.61 |
| `deadline_relocate` | Supplementary | 15,168 | 699 | 257,425.60 |
| `deadline_return_ties` | Supplementary | 15,222 | 645 | 179,078.70 |
| `deadline_size_ties` | Supplementary | 15,157 | 710 | 257,075.40 |
| `deadline_slack_limit` | Supplementary | 11,096 | 4,771 | 1,471,060.80 |
| `deadline_time_limit` | Supplementary | 15,222 | 645 | 179,004.33 |
| `deadline_trip_limit` | Main | 15,222 | 645 | 179,088.70 |
| `deadline_trip_wait_guard` | Supplementary | 15,222 | 645 | 179,088.70 |
| `deadline_two_opt` | Main | 15,177 | 690 | 255,466.93 |
| `deadline_window_departure` | Main | 15,180 | 687 | 242,935.56 |
| `holdback_h120` | Supplementary | 15,177 | 690 | 255,466.93 |
| `holdback_h30` | Supplementary | 15,202 | 665 | 292,565.53 |
| `holdback_h60` | Supplementary | 15,179 | 688 | 260,252.25 |
| `hybrid_u0` | Supplementary | 15,232 | 635 | 353,473.51 |
| `hybrid_u100` | Supplementary | 15,206 | 661 | 355,647.04 |
| `hybrid_u100_two_opt` | Supplementary | 15,177 | 690 | 255,466.93 |
| `hybrid_u25` | Supplementary | 15,217 | 650 | 351,446.84 |
| `hybrid_u25_two_opt` | Supplementary | 15,166 | 701 | 296,843.07 |
| `hybrid_u50` | Supplementary | 15,226 | 641 | 348,157.65 |
| `hybrid_u50_two_opt` | Supplementary | 15,170 | 697 | 286,071.79 |
| `hybrid_u75` | Supplementary | 15,217 | 650 | 354,452.67 |
| `hybrid_u75_two_opt` | Supplementary | 15,156 | 711 | 268,031.47 |
| `nearby_first` | Main | 15,232 | 635 | 353,473.51 |
| `nearby_local_search` | Main | 15,175 | 692 | 328,603.53 |
| `nearby_two_opt` | Main | 15,174 | 693 | 319,101.86 |
| `reserve_k1` | Supplementary | 15,136 | 731 | 229,641.92 |
| `reserve_k2` | Supplementary | 15,069 | 798 | 243,458.35 |
| `reserve_k3` | Supplementary | 15,090 | 777 | 230,509.94 |
| `reserve_k4` | Supplementary | 15,090 | 777 | 233,174.60 |
| `trip_limit_100` | Supplementary | 13,572 | 2,295 | 614,261.67 |
| `trip_limit_105` | Supplementary | 15,203 | 664 | 189,912.33 |
| `trip_limit_110` | Supplementary | 15,214 | 653 | 182,978.60 |
| `trip_limit_115` | Supplementary | 15,228 | 639 | 186,730.77 |
| `trip_limit_120` | Supplementary | 15,228 | 639 | 185,365.94 |
| `trip_limit_125` | Supplementary | 15,222 | 645 | 179,088.70 |
| `trip_limit_130` | Supplementary | 15,223 | 644 | 180,590.38 |
| `trip_limit_135` | Supplementary | 15,236 | 631 | 205,889.45 |
| `trip_limit_140` | Supplementary | 15,208 | 659 | 222,657.43 |
| `wait_f50` | Supplementary | 15,166 | 701 | 252,768.31 |
| `wait_f70` | Supplementary | 15,166 | 701 | 252,768.31 |
| `wait_f90` | Supplementary | 15,166 | 701 | 252,768.31 |
| `window_aware` | Main | 15,237 | 630 | 525,915.02 |
| `window_departure_compare` | Supplementary | 15,170 | 697 | 245,502.42 |
| `window_departure_post2opt` | Supplementary | 15,177 | 690 | 255,466.93 |

The report sensitivity claim refers to the original 35-policy pool, listed explicitly in `results/report_claim_checks.json`. It excludes the later time-limit and return-tie trials and the separately reported fixed-limit sweep. Later challengers have slightly lower penalties under some weights. The selected policy is retained under the stated adoption rule, rather than claimed to be the minimum across every explored variant.

The nine `trip_limit_*` modules were added so that each reported setting can be run on its own. The 100- and 140-minute logs were regenerated to verify the reported results. The other original results come from Git history or saved local experiment folders.

The modified-input stress results stay under `experiments/robustness-study-2026-11-04/`, separate from the original data and this table.
