# Supporting experiments

These folders preserve existing experiment records. They were copied into the submission staging folder on 5 November 2026. This date records the recovery, not the original experiment date.

| Folder | Evidence |
|---|---|
| `trip-limit-validation-2026-11-04/` | Seven trip limits, 140 policy-days, split-half calculations and validation script |
| `robustness-study-2026-11-04/` | Eight explicit input scenarios, five policies, 800 policy-days, transformed inputs and scripts |
| `time-limit-experiment-2026-11-04/` | Saved original-data trial used as a stress-study replay control |
| `return-tie-experiment-2026-11-04/` | Saved original-data trial used as a stress-study replay control |
| `runtime/` | Original runtime samples, machine details, benchmark script and 60 retained logs |

See `../docs/reproduction.md` for commands. Rerunning an experiment replaces its saved outputs. Runtime measurements will vary.

The selected policy is still `deadline_trip_limit`. These records do not establish performance on new demand or prove optimality. The later stress study uses a different candidate pool and explicit transformations, so its rankings should not be substituted for Chloe's earlier stress claims.

Historical draft notes were moved to a private backup outside this submission folder. Saved inputs, results, scripts and provenance manifests are retained here. Use the reproduction instructions for current commands.

`recovery_manifest.json` records source hashes and the five script path adjustments. No dispatch logic was changed during this recovery.
