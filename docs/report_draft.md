# Last-Mile Delivery Planning

Working draft for team review. Names, course details, references and the actual
assistance record still need completing. Page allocations below are a layout
plan, not a verified page count. The main report must fit within eight pages
excluding references after formatting and PDF export.

| Section | Planned pages |
|---|---:|
| Problem and metric | 1 |
| Algorithms and data structures | 2 |
| Complexity | 2 |
| Experiments and discussion | 2.5 |
| Conclusion | 0.5 |

## 1. Problem and objective

The task is to dispatch ten vehicles from a hub to deliver parcels arriving
throughout the day. Each trip must carry at most 30 capacity units, travel at
most 320 km including its return, and reach the hub by 18:00. Planning occurs
every ten minutes from 08:00 to 17:30. A confirmed trip departs 30 minutes
after planning; vehicles travel at 60 km/h and delivery service time is zero.
Delivery windows are preferences: early and late deliveries are permitted. [1]

A policy must decide which available parcels to carry, their delivery order,
and whether to dispatch now. These decisions interact. A route that improves
one trip's delivery times may return later and reduce opportunities to serve
other parcels. Only the current simulator snapshot is available to a policy;
future demand cannot be read from the input files during dispatch.

The chosen daily metric is

`P = 240U + E + L`,

where U is the number of undelivered parcels and E and L are total early and
late minutes among delivered parcels. Delivery at either window boundary has
zero timing penalty. An undelivered parcel receives only the fixed penalty.

This metric captures both completion and timing, unlike delivery rate alone.
The weight 240 is a modelling choice: leaving one parcel undelivered is treated
as equivalent to 240 accumulated minutes outside delivery windows. It is not
a monetary estimate. A delivery more than 240 minutes outside its window can
therefore cost more than leaving that parcel undelivered. The policies do not
explicitly drop parcels using that comparison. Sensitivity checks examine how
changing the weights affects the recommendation.

## 2. Algorithmic approaches

### Greedy construction

The supplied baseline considers parcels in arrival order. Deadline-first,
nearby-first and window-aware instead repeatedly rank the remaining eligible
parcels, append the first feasible one, and update the current location, load
and distance. All additions include the return leg in their feasibility checks.

| Constructor | Priority |
|---|---|
| Baseline | Arrival time, then ID |
| Deadline-first | Window end, current distance, then ID |
| Nearby-first | Current distance, window end, then ID |
| Window-aware | Next-leg travel time plus predicted early/late minutes; then distance, deadline and ID |
| Urgency hybrid | Deadline priority until a chosen fraction of capacity is filled, then nearby priority |

Greedy construction is fast and maintains a feasible route after each addition,
but an early choice can prevent a better combination later. Deadline-first
protects urgent parcels while its distance tie-break reduces unnecessary travel.
Nearby-first favours short movements but can delay urgent distant parcels.
Window-aware considers immediate timing, but its lowest-score rule can keep
postponing a parcel whose accumulated lateness makes its score large. These
heuristics do not solve the complete daily scheduling problem.

### Local search

Pair-swap search exchanges two selected parcel positions. The 2-opt variant
reverses a contiguous segment. Each starts from a feasible greedy route,
evaluates all moves in its neighbourhood and applies the best strict timing
improvement. Search stops when no feasible improving move remains. These are
adaptations of the greedy and local-search ideas covered in Week 11. [2, 3]

The objective within a fixed selected set is early plus late minutes; capacity
is preserved by reordering, while distance and return time are checked again.
Full-route evaluation is necessary in the current implementation because a
change affects subsequent arrival times. Full reversal is also considered:
equal-distance routes can have different timing penalties.

A local optimum need not be globally optimal. Reordering cannot replace the
selected parcels, and reducing a trip's timing penalty can worsen the day's
score by changing vehicle availability.

### Selection and waiting alternatives

The experiments also tested several changes to the construction or departure
choice:

- Candidate selection builds several hybrid + 2-opt routes and chooses by a
  trip-level score: timing minus 240 per carried parcel, optionally divided by
  distance. This score does not value all later consequences for parcels left
  at the hub.
- Holdback temporarily excludes parcels whose windows open much later, provided
  a later direct trip appears possible with a return margin.
- Wait-to-fill delays an underfilled route unless a load, urgency, elapsed-wait
  or late-day condition calls for departure.
- Return-time caps limit how much 2-opt may extend the initial greedy trip.
- Backfill tries adding waiting parcels at every route position. Exchange tries
  replacing one selected parcel with two waiting parcels. Both accept strict
  improvements in timing minus 240 per carried parcel and rerun 2-opt.
- Relocation moves one selected parcel to another position, alternating with
  2-opt. A separate size-tie variant favours smaller parcels only after equal
  deadline and distance priorities.

### Selected policy: deadline-first with window-aligned departure

`deadline_window_departure` first constructs the deadline-first route and
projects its stop-by-stop arrivals, including preparation time. If every
selected delivery would be at least ten minutes early and delaying the fixed
route by ten minutes still allows return by 18:00, it returns an empty list.
The vehicle remains idle for this round. Otherwise, it improves the route with
2-opt and dispatches it.

The next planning round constructs a fresh route from the parcels then
available. No parcels are reserved and no future arrivals are predicted.
The check shows that postponing the current fixed route is feasible; it does
not guarantee that the next round will choose that same route. The eventual
confirmed trip has the simulator's normal single preparation delay.

This differs from waiting for a fuller load. In the recorded replay, all 352
deliberate deferral decisions had planned loads of at least 27 out of 30.
The rule targets avoidable earliness even when the van is nearly full.

### Data structures

Lists store delivery order and support sorting, swapping and segment reversal.
Parcel dictionaries and the nested directed-distance dictionary provide average
constant-time lookups during candidate evaluation. Sets support membership
checks for selected or held parcels. These structures directly support route
construction and neighbourhood evaluation rather than serving as unused
additions. The distance interface is treated as directed even though the supplied
matrix is symmetric.

## 3. Time and space complexity

For one dispatch call, let n be all supplied parcel records, m eligible parcels,
k selected parcels, and R complete local-search scans including the final failed
scan. Dictionary/set access is average O(1), IDs are bounded in length, and
numeric operations are constant time. Extra space excludes input snapshots.
Define `G = n + 1 + (k+1)m log(m+1)` and `L = 1 + k + Rk³`.

| Family | Time per dispatch | Extra space |
|---|---|---|
| Baseline | O(n+1+m log(m+1)) | O(m+1) |
| Repeated-sort greedy, including hybrids and size ties | O(G) | O(m+1) |
| Greedy + pair swaps / 2-opt | O(G+L) | O(m+k+1) |
| q candidate routes, evaluated sequentially | O(Σ(G_j+L_j)) | O(m+K+q+1) |
| Holdback + 2-opt | O(n+1+G(n',m',k)+L) | O(n+k+1) |
| Wait-to-fill / return cap | O(G+k+L) | O(m+k+1) |
| Window-aligned departure | O(G+k) when deferred; O(G+k+L) otherwise | O(m+k+1) |

Filtering takes O(n). Baseline sorts once. Other constructors sort after each
accepted addition, with up to one final unsuccessful round; scans and list
removal are linear and covered by G. For k=m, the greedy bound becomes
O(n+1+m² log(m+1)).

Each local-search scan evaluates O(k²) moves. Copying and evaluating a candidate
route take O(k), so a scan costs O(k³). The complete search includes R scans,
not just one. Strict improvements and finitely many permutations ensure
termination without establishing a polynomial bound on R. The lecture's
constant-time distance-delta evaluation for symmetric distance-only 2-opt does
not apply to this full timing evaluation. Only a few candidate routes are kept
at once, so space remains linear.

Candidate selection retains the best and current route, not all q routes.
Holdback's shallow visible-parcel dictionary can contain O(n) records even
when few are waiting. Wait-to-fill runs 2-opt before deciding to wait; the
window-aligned rule skips it on deferred calls.

For the additional improvement experiments, let k₀ be initial route length,
K the largest route reached, B accepted insertions/exchanges and R_total all
2-opt scans across restarts. Define `G₀=G(n,m,k₀)` and
`L_total=B+1+(B+1)K+R_total K³`.

| Experiment | Time per dispatch | Extra space |
|---|---|---|
| Backfill | O(G₀+(B+1)[1+m(K+1)²]+L_total) | O(m+K+1) |
| Exchange | O(G₀+(B+1)[n+1+m log(m+1)+K log(K+1)+r w²(K+1)]+L_total) | O(m+K+r+w+1) |
| Relocation | O(G₀+1+(A+1)(k+1)+(A+R_total)k³) | O(m+k+1) |

Backfill tries m parcels in up to K+1 positions with linear evaluation.
Exchange sorts all candidates before retaining w<=8 waiting and r<=4 selected
parcels, then evaluates O(rw²) replacements. Each accepted insertion/exchange
increases selected count, so B<=m-k₀. Relocation keeps k fixed and makes A
relocation scans, each costing O(k³), restarting 2-opt after an improvement.
A, like R_total, has no demonstrated polynomial bound.

Daily policy time sums these bounds over actual dispatch calls, including calls
that return no route. Waiting can increase the number of calls. Simulator
snapshot copying, events and logging are additional costs. Therefore per-call
complexity and measured full-day runtime answer different questions.

## 4. Experimental results and discussion

### Setup and baseline diagnosis

All policies use the same 20 supplied days, totalling 15,867 parcels, under
identical operating constraints. Each successful run produces an event log and
metrics report. The saved results contain 34 parameter/policy variants, not
34 unrelated algorithm families. Daily penalties are summed for comparison.
All days informed development; the two ten-day blocks are robustness checks,
not training and untouched test sets.

Baseline delivers 6,421 parcels (40.47%) and scores 2,702,047.24. Across its
200 first trips, average load utilisation is 26.03% and average distance is
285.51 km. This suggests that poor spatial ordering and long trips limit
performance even when substantial capacity is unused. It does not isolate
capacity as the sole cause.

### Main comparison

| Policy | Delivered | Penalty |
|---|---:|---:|
| Baseline | 6,421 | 2,702,047.24 |
| Deadline-first | 15,206 | 355,647.04 |
| Nearby-first | 15,232 | 353,473.51 |
| Window-aware | 15,237 | 525,915.02 |
| Nearby + pair swaps | 15,175 | 328,603.53 |
| Nearby + 2-opt | 15,174 | 319,101.86 |
| Deadline + 2-opt | 15,177 | 255,466.93 |
| Window-aligned departure + deadline + 2-opt | 15,180 | 242,935.56 |

The most deliveries do not necessarily give the best chosen score. Window-aware
has the highest completion count in this table but much higher lateness.
Deadline + 2-opt improves on nearby + 2-opt on all 20 days, reducing aggregate
penalty by 19.94%. The initial selection therefore matters even when both
policies use the same subsequent neighbourhood search.

The selected departure policy improves on deadline + 2-opt on 16 days and
worsens four. Its total reduction is 12,531.37 points (4.905%). Undelivered
parcels fall from 690 to 687, early minutes from 12,258.57 to 1,871.91, and late
minutes from 77,608.36 to 76,183.63. Timing accounts for most of the improvement.

The existing adoption rule requires at least 2% lower penalty on days 11–20
and no increase on days 1–10. The departure policy improves those blocks by
5.650% and 4.057%, respectively. Wait-to-fill scores 252,768.31 overall but
worsens the first block, so it failed that rule. The selected policy improves
on both its aggregate score and the reference's.

### What the unsuccessful tests show

| Follow-up | Penalty | Finding |
|---|---:|---|
| Return caps 0 / 15 / 30 minutes | 308,215.69 / 284,770.55 / 271,665.53 | Shorter return times did not compensate for added earliness |
| Backfill | 255,240.88 | Small improvement; below the adoption threshold |
| One-for-two exchange | 527,602.03 | Better reduced packings did not improve the daily schedule |
| Relocation | 257,425.60 | Escaping some route local optima did not improve the aggregate score |
| Smaller-size tie-break | 257,075.40 | More daily wins did not imply lower aggregate penalty |

Candidate-selection variants score between 288,651.61 and 304,815.10; the tested
holdback variants do not beat the deadline + 2-opt reference. These results
show the limits of optimising a current-trip proxy. For example, exchange
repairs reduced packing counterexamples but completes 791 fewer parcels than
the reference over full days. Neglecting later service opportunities is a
plausible explanation, not an isolated causal proof.

A separate exact search examined 15 bounded cases with at most eight parcels.
It exposed both selection gaps and order local optima. These deliberately
small, selected cases are useful counterexamples, but their single-trip proxy
cannot prove which full-day policy is best. Factorial enumeration is unsuitable
as the main dispatcher.

### Sensitivity, runtime and checks

The selected policy ranks first among saved variants at undelivered weights
120, 240 and 480 with equal early/late weights. It remains first with early
weights 0.75 or 0.5 and late weight 1, and with early weight 1 and late weight 2.
At early weight 0.25, the 30-minute return cap narrowly leads; when early
penalties are removed, `hybrid_u50` leads. Thus the recommendation depends on
valuing earliness. These are fixed-policy rescores, not retuned algorithms.

Both the reference and selected policy were benchmarked with a warm-up and
three repetitions of all 20 days, alternating order. Median total simulation
time was 5.40 versus 5.98 seconds. Policy-only medians were 2.70 versus
2.39 seconds. Extra planning and simulator overhead can increase total runtime
even when policy-only time falls. Timings exclude metric calculation and
interpreter startup and depend on the machine.

Trip checks cover capacity, round-trip distance, return cutoff, parcel
availability, duplicate deliveries and arrival-time consistency. Metrics were
recomputed from logs, and repeated benchmark replays matched saved logs. These
checks support correctness on the recorded runs; they do not establish
optimality or performance under every possible input.

## 5. Conclusion

Deadline-first selection, window-aligned departure and 2-opt provide the best
aggregate chosen score among the tested variants. The policy improves timing
substantially while completing slightly more parcels than deadline + 2-opt.
It also passes the existing adoption rule across both development blocks.

The experiments show why trip packing, route order and departure timing must
be evaluated through the complete simulator. Improvements to a reduced case
or a single-trip objective can damage later service. The final recommendation
is supported by these historical results, with slightly higher measured total
runtime, an objective-dependent ranking and no untouched evaluation set.

## References and items to complete

[1] IS115 Project Brief. Cite the supplied version; operating model p. 1,
requirements/deliverables p. 5 and rubric/AI rules p. 6.

[2] IS115 Week 11, *Heuristics Part 2a - Greedy Algo*. Complete the lecturer,
year and citation format from the supplied course material.

[3] IS115 Week 11, *Heuristics Part 3 - Local Search*. Complete the lecturer,
year and citation format from the supplied course material.

Reproducibility: see the repository README and `docs/reproduction.md`.
Detailed experiment evidence is in `docs/experiment_notes.md` and
`docs/followup_search_results.md`; full complexity derivations are in
`docs/complexity_analysis.md`. Supporting files do not replace the required
explanations in the submitted eight-page report.

Before treating this as submission-ready:

- Both teammates must review the reasoning and confirm they can explain the
  implementations, metric and rejected alternatives themselves.
- Add team/course details, complete source citations and verify the formatted
  main report is no more than eight pages, excluding references.
- Include the actual prompts and responses required by the brief. The current
  AI record is incomplete. The brief permits only the supplied Gemini Gem for
  boilerplate coding and requires students to formulate the algorithms; use
  of other assistance needs an honest account and lecturer clarification on
  any required remediation. Rewriting this draft does not resolve that issue.
- Check the final ZIP contains the required code, logs, metrics, README and
  report, including supporting scripts/docs referenced by its run instructions.
