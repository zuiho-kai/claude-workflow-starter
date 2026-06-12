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
| Benchmark metric definitions, smoke vs sweep, scope lock, result naming | [benchmark_scope.md](plan_and_validation/benchmark_scope.md) |
| Long remote validation, existing script reuse, profiler isolation | [remote_long_run.md](plan_and_validation/remote_long_run.md) |

Hard-rule summary:

- Trace the lifecycle before proposing an implementation plan.
- Feature validation defaults to the real e2e path. Fake/unit tests only prove local helper behavior.
- Benchmark first locks version, measurement patch, code path, and valid metrics.
- Reuse a known working script or runbook before writing a new runner.
