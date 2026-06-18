---
name: Plan and validation routing
description: Route planning, e2e validation, benchmark scope locks, and long remote run checks.
type: feedback
---

# Plan / Validation Entry

This file is only a router. Open the topic that matches the task instead of loading every historical runbook.

| Task | Read this |
| --- | --- |
| Plan writing, feature viability, e2e vs fake/unit, performance evidence chain | [core_validation.md](plan_and_validation/core_validation.md) |
| Benchmark metric definitions, smoke vs sweep, scope lock, result naming, PR/spec source-of-truth checks | [benchmark_scope.md](plan_and_validation/benchmark_scope.md) |
| Long remote validation, existing script reuse, profiler isolation | [remote_long_run.md](plan_and_validation/remote_long_run.md) |
| Graph/profiling diagnosis, request-window capture, trace-quality gates | [profiling.md](remote_debug_strategy/profiling.md) |

Hard-rule summary:

- Trace the lifecycle before proposing an implementation plan.
- Feature validation defaults to the real e2e path. Fake/unit tests only prove local helper behavior.
- Benchmark first locks version, measurement patch, code path, and valid metrics.
- If the user points to a PR, issue, config, or benchmark spec, read that object’s real config, runner/client, result JSON/artifact, and metric definitions before answering.
- Classify evidence as strict apples-to-apples, workload-aligned only, or smoke only before making any performance claim.
- Keep L2 mock/CPU functional guards separate from L4 real-weight accuracy/performance/profiling evidence.
- Reuse a known working script or runbook before writing a new runner.
- Concrete host, artifact, PR, and path facts belong in private archive/runbook pages; public docs should keep only decision gates, execution order, evidence gates, and stop conditions.
