# Remote Long Runs

Long remote validation is expensive. Prove the configuration chain before burning GPU time:

- generated config or CLI arguments
- normalized engine/runtime arguments
- worker/backend log confirming the intended path
- single request or minimal smoke
- artifact directory and cleanup plan

## Script Reuse

If a previous script or runbook has already succeeded on the same class of task, reuse it with minimal changes. Do not rewrite an equivalent runner unless the old route is impossible or unsafe.

## Profiler Isolation

Profiling code must not change steady-state behavior unless the measurement scope explicitly says so. Keep probe patches behind an explicit flag, environment variable, or one-off script. Mark runs that include probes separately from production-path runs.

## Stop Conditions

Stop and report a blocker when logs show dependency compilation stalls, missing cache roots, shared-memory waits, authentication failures, or repeated environment setup failures. Treat those as environment blockers, not slow model execution.
