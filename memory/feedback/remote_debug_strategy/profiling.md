# Profiling

Profiling is a state machine. Do not collapse service readiness, request completion, trace export, profiler shutdown, benchmark wrapper exit, local artifact save, and resource cleanup into one vague "done".

If the user asks for profiling, trace, operator timing, flame graph, timeline, Perfetto, Chrome trace, or Nsight, default to a trace artifact. Result JSON, stage durations, throughput tables, and latency summaries are benchmark evidence, not trace profiling.

## Scope

A profiling run needs:

- exact code path
- warmup policy
- start/stop trigger
- profiler output directory
- trace quality checks
- cleanup plan

For graph or compiled execution, first prove the pure graph path with the smallest variable set. Add profiler instrumentation only after health check, one-request smoke, and formal benchmark path are understood.

For graph or compiled-mode claims, the minimum provenance is same-run evidence for:

- server command/log proving graph or compiled mode
- target request log or JSON proving success and workload match
- trace file mtime/export log overlapping the profiling start/target request/stop window
- event summary showing the categories needed for the question, such as CPU ops, CUDA runtime/kernel, communication, or framework events
- resource cleanup proving the run is not still occupying the machine

If any item is missing, report the separate facts you have: graph benchmark status, trace existence, whether the trace belongs to graph mode, and cleanup status. Do not combine an eager trace with a graph benchmark into one graph profiling conclusion.

## Probe Discipline

Probe patches must be explicit. If a probe changes scheduling, synchronization, logging volume, or data movement, mark the run as probe-only and do not compare it to production steady state.

## Trace Quality

Before interpreting a trace, confirm:

- trace files exist and are non-empty
- expected ranks/workers emitted data
- profiling window overlaps the target request
- metric counters are nonzero for the reported metric

Empty traces, zero-count metrics, and startup-only captures are invalid evidence.

If a full request-window trace kills the worker, fails to export, or returns an empty profiler stop response, call it a full-trace capture failure. A shorter bounded smoke trace can validate profiler plumbing, but it should not be presented as the formal profiling result.

## Request-Window Capture

For endpoint-controlled profilers, capture the workload window explicitly:

1. Confirm the service is healthy and profiler endpoints/routes are enabled.
2. Start profiling.
3. Run the exact target request or benchmark workload.
4. Stop profiling immediately after the target workload completes.
5. Verify trace files and metric counters before interpreting them.

Bounded smoke traces can prove profiler plumbing, rank coverage, and export logic. They do not prove full-request performance unless the capture window covers the real request.

## Status States

Report progress with these states:

| State | Evidence |
| --- | --- |
| service ready | health check succeeds; profiler run also has profiler routes enabled |
| request done | target endpoint returned success or benchmark progress reached 100% |
| trace exported | expected trace files exist and sizes are stable |
| profiler stopped | stop endpoint/log succeeded |
| benchmark done | benchmark wrapper exited and result file exists |
| local artifact saved | archive and extracted trace files exist locally |
| resources released | this run's process group is gone and GPU/port/process checks are clean |

If only some states are true, say exactly which ones are complete.

## Trace Quality Gate

Before delivery, summarize trace quality from the trace itself:

- file sizes
- event counts
- rank/worker coverage
- process/thread counts when relevant
- top event categories
- presence of CPU ops, Python functions, CUDA runtime/kernel events, communication events, or framework-specific events required by the task

Do not treat empty stack files as a standalone failure; inspect event categories and names. Conversely, do not treat "a trace file exists" as success when it lacks the categories needed for the user's question.

## Artifact And Cleanup Order

Recommended order:

1. Confirm remote trace/result files exist.
2. Create a single archive and list its contents.
3. If resources are scarce, release the service process group after archive verification.
4. Download and extract the archive locally.
5. Re-check remote processes, ports, scheduler state, and GPU memory.

Final reports should include artifact paths and resource-release evidence. A successful profiler stop is not the same as resource cleanup.
