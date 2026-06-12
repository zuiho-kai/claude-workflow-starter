# Benchmark Scope

Benchmark work starts with a scope lock:

- measured version or commit
- measurement patch, if any
- exact code path and entrypoint
- input set and run count
- warmup policy
- metrics that are valid for this run
- metrics that must be marked unavailable
- artifact directory and naming convention

## Evidence Tiers

- Exploration: proves a command shape or parameter route.
- Smoke: proves the path can complete once.
- Sweep: repeated runs with stable scope; this is the first tier that can support performance claims.

Never compare exploration output to a formal sweep. If metric count is zero or the trace is empty, report that metric as unavailable instead of filling in a number.

## Reporting

Include:

- commit or version
- command or script path
- run count
- input scope
- raw artifact path
- known limitations

For latency work, separate setup/init time, request wall time, and per-step/per-token metrics when the system exposes them.
