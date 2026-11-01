# Further targeted tests: selection, neighbourhood and departure timing

Date: 1 November 2026. Reference: Chloe's `deadline_two_opt` from commit
`8c77d42`. Experiments are on `codex/return-time-caps` and were pushed in
commit `c23011e`. No original policy or saved reference result was changed.
The shared document was not updated during this follow-up. Later documentation
and helper-layout edits should be checked separately in Git status.

## Rules fixed before each full experiment

The main metric remains 240 per undelivered parcel plus early and late minutes.
Use the existing adoption rule: at least 2% lower penalty on days 11–20 and no
higher penalty on days 1–10. The split is development evidence, not a held-out
test. These follow-ups are exploratory and adaptive; do not describe their
comparison as a preregistered statistical trial.

1. **One-for-two exchange (`deadline_exchange`).** Start with deadline + 2-opt.
   In each round consider the four largest selected parcels and eight smallest
   waiting parcels, breaking the stated ties deterministically. Replace one
   selected parcel with two adjacent waiting parcels at its position, trying
   both orders. Accept the best feasible strict improvement to timing minus
   240 per carried parcel, then rerun 2-opt. Repeat. Every exchange adds one
   selected parcel, ensuring termination. This repairs the two reduced packing
   counterexamples, including the three-versus-six-parcel case, but its
   trip-level objective ignores later service of the parcel left behind.
2. **Single-parcel relocation (`deadline_relocate`).** Preserve the selected
   set; move one parcel to any other route position. Accept the best feasible
   strict timing improvement and rerun 2-opt. Repeat until neither this move
   nor a reversal improves timing. It reaches the exact same-set optimum in
   two reduced cases where the original 2-opt was stuck. Capacity selection
   gaps remain outside its neighbourhood.
3. **Smaller-size tie-break (`deadline_size_ties`).** Keep deadline, then
   current-distance priority; add parcel size before parcel ID only when both
   previous priorities tie. Apply the unchanged 2-opt. This tests a narrower
   packing improvement without deliberately replacing a more urgent parcel.
4. **Window-aligned departure (`deadline_window_departure`).** Construct the
   original deadline-first route and project its actual stop-by-stop arrival
   times, including the 30-minute preparation delay. If every selected parcel
   would arrive at least 10 minutes before its window starts, and that route
   could still return by 18:00 after a 10-minute delay, return an empty route
   for this planning round. Reconsider all currently available parcels at the
   next round. Otherwise apply the unchanged 2-opt and dispatch normally.

The departure rule does not reserve parcels, predict future arrivals, add
waiting at customer stops, make delivery windows hard, or add an extra
preparation delay. Returning [] leaves the van idle; the simulator's eventual
confirmed trip incurs its usual single 30-minute preparation. A changed next
snapshot may lead to a different route. The safety check concerns the current
fixed route, not a prediction of future demand or route choices.

This is different from Chloe's under-filled waiting rule. In the replay,
there were 352 deliberate deferral decisions and all had planned loads of
at least 27 out of 30. The new rule waits for a suitable time even when the
van is full; it is not trying to accumulate more load.

## Full-day results

| Policy | Delivered | Early minutes | Late minutes | Penalty | Change vs reference |
|---|---:|---:|---:|---:|---:|
| Reference: deadline + 2-opt | 15,177 | 12,258.57 | 77,608.36 | 255,466.93 | — |
| One-for-two exchange | 14,386 | 2,265.62 | 169,896.39 | 527,602.03 | +106.525% |
| Relocation + 2-opt | 15,168 | 11,952.21 | 77,713.40 | 257,425.60 | +0.767% |
| Smaller-size tie-break | 15,157 | 10,624.84 | 76,050.59 | 257,075.40 | +0.630% |
| Window-aligned departure | 15,180 | 1,871.91 | 76,183.63 | 242,935.56 | −4.905% |

| Policy | Days 1–10 | Change | Days 11–20 | Change | Daily wins/losses/ties | Adopt? |
|---|---:|---:|---:|---:|---|---|
| Reference | 119,444.44 | — | 136,022.49 | — | — | Reference |
| Exchange | 262,908.74 | +120.110% | 264,693.29 | +94.595% | 0 / 20 / 0 | No |
| Relocation | 120,570.67 | +0.943% | 136,854.93 | +0.612% | 3 / 4 / 13 | No |
| Smaller-size tie-break | 123,209.68 | +3.152% | 133,865.72 | −1.586% | 13 / 7 / 0 | No |
| Window-aligned departure | 114,598.45 | −4.057% | 128,337.11 | −5.650% | 16 / 4 / 0 | Yes |

## Interpretation and current recommendation

The exchange result demonstrates that solving reduced packing counterexamples
does not imply a better full-day dispatcher. It completes 791 fewer parcels
and more than doubles total penalty. Relocation improves bounded route orders
but still slightly worsens the full-day score. The size tie-break fails the
decision rule despite improving more individual days than it worsens: total
magnitude and the split criterion matter, not only win counts.

**Current recommendation: `deadline_window_departure`.** It passes the
existing adoption rule, has the lowest aggregate main-metric score among the
saved policies, and improves on 16 of the 20 days. It also beats wait-to-fill's
252,768.31 aggregate penalty, so the previous lowest-total/adoption-rule
distinction is no longer needed for the main recommendation on these runs.

Against `deadline_two_opt`, the new method has three fewer undelivered parcels,
10,386.66 fewer early minutes and 1,424.73 fewer late minutes. Thus it improves
all three aggregate components: any non-negative weighting of these components
with at least one positive weight prefers it to that reference on these days.
That statement is about the aggregate component totals, not every day, every
alternative method, or unseen data. Its main gain is timing, not delivery count.

Driving distance also falls from 86,847.264 km to 81,748.365 km, even though
the new method makes 639 trips versus 635. This is consistent with replacing
some timing-improving detours by deliberate hub deferral. It does not isolate
every causal effect because the full schedule and later selections change.

## Sensitivity

Rescoring every saved policy using rounded component fields gives:

- At undelivered weights 120, 240 and 480, with early/late weights both 1,
  window-aligned departure ranks first.
- With undelivered weight 240, early weights 0.75 or 0.5 and late weight 1,
  it still ranks first; with early weight 1 and late weight 2 it also ranks first.
- With early weight 0.25 and late weight 1, `deadline_cap30` ranks first,
  narrowly ahead of the new policy.
- If early deliveries are free, `hybrid_u50` ranks first among all currently
  saved variants. Do not reuse the earlier claim that deadline-first is best
  across an expanded set of policies without recalculating the ranking.

These are fixed-policy rescores, not reoptimisation for each metric. Rounding
can change totals by a few hundredths; the main table sums stored daily
`total_penalty` values. All 20 days were used for development and evaluation.

## Reproduction

```bash
python3 run_all.py solution.policies.deadline_exchange deadline_exchange
python3 run_all.py solution.policies.deadline_relocate deadline_relocate
python3 run_all.py solution.policies.deadline_size_ties deadline_size_ties
python3 run_all.py solution.policies.deadline_window_departure deadline_window_departure
python3 check_trips.py deadline_exchange deadline_relocate deadline_size_ties deadline_window_departure
python3 benchmark_followups.py
```

Daily logs/metrics are in the corresponding results folders. Supporting files:
`results/followup_policy_summary.json`, `results/window_departure_sensitivity.json`,
`results/window_departure_diagnosis.json`, and `results/followup_benchmark.json`.

## Validation and runtime

All 80 daily reports were recalculated and matched. Across 2,488 new trips,
checks found no hard-constraint violations, duplicate deliveries, delivery-time
inconsistencies or parcels selected before availability at planning. Checks on
the 15 bounded cases and synthetic packing/eligibility cases verified each
operator's intended behaviour and unchanged inputs. The departure rule was
checked for its wait trigger, dispatch once windows approach, and return guard.

The reference and departure policy were each rerun three times across all
20 days after a day-1 warm-up, alternating policy order. Every replay log
matched its saved result exactly. Median total simulation time was 5.40 s for
the reference and 5.98 s for departure alignment. Policy-only medians were
2.70 s and 2.39 s; increased planning calls/snapshot overhead can make total
runtime higher despite lower time inside the policy. Timings exclude metric
calculation, interpreter startup and replay-file comparison.

The new decision adds O(k) work to inspect the constructed route, plus its
original greedy construction and, on dispatched routes, its original 2-opt
work. Across a full day it can cause more dispatch calls. Do not claim that
waiting removes simulator work or guarantees a smaller asymptotic running time.
See [complete complexity analysis](complexity_analysis.md) for the per-call
and whole-day bounds across every policy family.

The recommended change is supported by these experiments, not a proof of
global optimality or a promised grade. Preserve unsuccessful variants as
evidence, retain the development-data limitation, and accurately record the
assistance used for the follow-up work.
