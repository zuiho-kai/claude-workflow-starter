# Profiling

## Scope

A profiling run needs:

- exact code path
- warmup policy
- start/stop trigger
- profiler output directory
- trace quality checks
- cleanup plan

## Probe Discipline

Probe patches must be explicit. If a probe changes scheduling, synchronization, logging volume, or data movement, mark the run as probe-only and do not compare it to production steady state.

## Trace Quality

Before interpreting a trace, confirm:

- trace files exist and are non-empty
- expected ranks/workers emitted data
- profiling window overlaps the target request
- metric counters are nonzero for the reported metric

Empty traces, zero-count metrics, and startup-only captures are invalid evidence.
