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

## PR / Spec Source Of Truth

When the user asks about a PR, issue, benchmark spec, config, or "that setup", anchor the object before answering or launching a new run:

```text
Spec gate
- Target object:
- Source read: PR/config/runner/client/result JSON/artifact:
- Tested head or version:
- Dependency/runtime version:
- Model repo or local snapshot:
- Pipeline/class and endpoint:
- Workload: resolution, frames/fps, steps, prompt, negative prompt:
- Request contract: num prompts, warmup, request rate, max concurrency:
- Runtime contract: compile/eager, GPU, cache/offline env:
- Metric fields and units:
- Valid answer scope: strict / workload-aligned only / smoke only:
```

PR bodies and old summaries are indexes, not the full source of truth. For performance numbers, confirm the config and runner/client interpret the same metric the same way. Searching local leftovers is allowed for provenance, but it must not override the object the user pointed at.

Use field names and units when reporting results. Do not mix pytest wall time, startup time, stage duration, profiling duration, and request e2e latency.

## Evidence Tiers

- Exploration: proves a command shape or parameter route.
- Smoke: proves the path can complete once.
- Sweep: repeated runs with stable scope; this is the first tier that can support performance claims.

Never compare exploration output to a formal sweep. If metric count is zero or the trace is empty, report that metric as unavailable instead of filling in a number.

## Result Classification

Classify performance evidence before drawing a conclusion:

| Class | Meaning | Allowed Conclusion |
| --- | --- | --- |
| `strict apples-to-apples` | same model/checkpoint, pipeline semantics, request path, defaults, workload, runtime mode, and metric definition | framework or PR-level performance claim |
| `workload-aligned only` | workload shape matches, but one or more model/path/default/runtime details differ | observation under this workload only |
| `smoke only` | one or few runs prove the path can complete | path availability, not speedup |

If a run uses a different connector, backend, cache state, compile mode, prompt source, or metric parser, say so in the class. Do not hide those differences in a footnote and still claim strict comparison.

## Result Gate

Before putting a benchmark result into a PR body, docs page, or reviewer reply, check:

```text
head or version matches the scope lock
result JSON exists and belongs to the current run directory
completed requests match requested prompts
failed requests are zero, or failures are classified
startup log proves the intended backend/config/path flags were parsed and effective
metric counters are nonzero for every reported metric
cleanup status is known
```

If the run used the wrong head, wrong workload, wrong deploy/config, wrong endpoint, or a client-side concurrency setting that did not trigger the intended server path, mark it invalid for the current request instead of repackaging it.

## Reporting

Include:

- commit or version
- command or script path
- run count
- input scope
- raw artifact path
- known limitations

For latency work, separate setup/init time, request wall time, and per-step/per-token metrics when the system exposes them.
