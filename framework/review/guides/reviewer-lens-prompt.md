# Reviewer Lens Prompt

Use this when spawning a read-only review sub-agent. Do not add a suspected root cause unless the task is explicitly finding-closure for an already accepted finding.

```text
Static review this PR/diff/change. Do not stop after the first valid finding.
First classify the change by risk type, then audit every selected risk type.

Return all matching risk tags with one file/function evidence each:
- public API / user-facing contract
- module semantic contract
- cross-module producer-consumer contract
- async / concurrency / scheduling
- resource lifetime / cleanup
- data format / serialization / IPC
- performance claim / benchmark evidence
- error handling / cancellation / timeout
- feature flag / config / default behavior
- backward compatibility
- test or validation evidence

Then list selected review lenses. For EACH of the four base audits below,
return findings (P0 blocker / P1 should-fix / P2 nit) OR explicitly write
"none found" — do not skip any audit and do not pre-focus on one over another.

# Audit 1 — Duplication
Grep both the repo (project source dirs, scripts, tests, docs as applicable) and
any upstream/reference implementation for functions / classes / algorithms /
constants that overlap with anything new in this PR. List each match with:
  - file:line of the existing implementation
  - file:line of the new implementation
  - 1-line judgment: should reuse / cannot reuse + why

# Audit 2 — Layering
For each new piece of logic, identify which module persistently holds the data
it operates on. If logic and data live in different modules, list:
  - new logic location
  - data owner location
  - proposed correct home

# Audit 3 — Edge cases
List every range / boundary / default value the new code touches. For each,
name which branches handle:
  - empty / single-element / max-size extremes
  - non-contiguous ID ranges, off-by-one
  - None vs 0 vs sentinel
  - feature-flag matrix and old/new execution modes
Flag any boundary not explicitly handled.

# Audit 4 — Surface area
List every new public knob (CLI arg / API field / extra_args key / config
option / public function / SSE or OpenAI-compatible response chunk). For each:
  - If this is a request parameter, extra_body/extra_args key, processor kwarg,
    multimodal key, or cross-module bridge field, provide a contract matrix:
    ingress path(s), allowed value shapes, normalization point, owner module,
    downstream consumer(s), no-op cases, docs, and tests.
  - Can it be derived from existing knobs? If yes, why expose it?
  - Why is the default what it is? Can the help text be shorter?
  - Is the same value also expressible via another path?
  - If this is a public API field or response schema, where is the protocol type
    defined, where is it documented, and what bad-path tests cover it?
  - If this is streaming/SSE/WebSocket, which existing endpoint pattern and
    output-processor mechanism does it reuse?
  - If this is an internal optional fast-path parameter, what are its data
    contract and execution-context contract, and where does a wrong caller fail?
  - If this changes a shared state/schema type, list every constructor, unpack
    site, and consumer found by grep, and state how positional arity remains
    compatible.
Flag knobs that are accreted/over-defensive.

# Conditional audit — Path matrix
Run this when the change touches execution flow, feature flags, public contracts,
runtime behavior, async/concurrency, resources, or performance. For each
applicable path, provide checked evidence or "missing":
  - normal old path
  - normal new path
  - feature disabled
  - feature enabled
  - single request / single caller
  - concurrent requests / multiple callers
  - streaming or async event-loop path
  - low-resource / offload / constrained mode
  - public/direct caller and internal caller
  - test/benchmark path
Flag paths that only work on the happy path.

# Conditional audit — Resource lifecycle
Run this when the change allocates or passes files, memory, shared memory,
sockets, threads, tasks, processes, GPU buffers, pinned memory, locks, caches,
temp dirs, handles, or background work. For each resource, list:
  - allocated where
  - owner
  - passed to whom
  - consumed where
  - released where
  - allocation-failure behavior
  - failure-after-partial-allocation behavior
  - timeout/cancellation/shutdown behavior
  - concurrency bound
  - blocking point
  - test or evidence
Flag leaks, unbounded work, blocked event loops, swallowed failures, and
consumer hangs.

# Conditional audit — Evidence / benchmark
Run this when the change claims performance, quality, reliability, accuracy,
compatibility, or regression safety. Verify:
  - baseline and current runs are same hardware/input/config
  - warmup/compile/cold-start are separated
  - concurrency/request rate matches the claim
  - metric definition and sample count are clear
  - mean/median/stddev or repeated runs are sufficient for the claim
  - quality/accuracy/VRAM/resource regressions are ruled out
  - PR body evidence matches current head
  - screenshots are not the only proof
Flag unproven claims as findings.

Return findings in markdown. For each finding, first state:
1. what bad thing can happen;
2. why this PR owns it;
3. the smallest acceptable fix.
End with one line:
"RISK TAGS: ...; LENSES: ...; AUDITS RUN: 1,2,3,4[,path,lifecycle,evidence] — N findings (Pa P0, Pb P1, Pc P2)".
```

## Owner prompts

New model / pipeline / backend work needs two owner framings before the first public push:

```text
Role A: module owner. Review semantic parity against upstream. Treat shape-clean
and strict load as weak evidence. Check scheduler / denoising loop, embedding
order, activation, token order, special token + pad/eos attention mask,
preprocess, noise/action contracts, and real-checkpoint fail-fast behavior.
Return P0/P1/P2 findings only.

Role B: project/integration owner. Review whether this integration matches the
repository architecture. Check file/module ownership, public API surface, test
placement, stub-vs-real evidence separation, PR body reproducibility, and
whether any generic helper leaks caller-specific semantics. Return P0/P1/P2
findings only.
```

Rule: Role A answers "does it preserve the module/domain semantics"; Role B
answers "does it fit the project". Either side looking only at shape / smoke is
not enough.

## Specialist owner prompts

Add these when risk tags require them. Do not replace Role A/B unless the change
is purely in that specialty.

```text
Role C: systems / runtime owner. Review resource lifetime, concurrency, failure
propagation, blocking behavior, thread/process/task boundaries, IPC or
serialization, GPU/CPU transfer, scheduler/event-loop impact, locks, caches,
and cleanup. Build a lifecycle table for every resource and a path matrix for
normal, disabled, concurrent, error, timeout, cancellation, and shutdown paths.
Return P0/P1/P2 findings only with file/function evidence.

Role D: evidence / benchmark auditor. Review whether the PR evidence proves the
claim. Check baseline parity, workload/config/request propagation, warmup or
compile exclusion, concurrency/request-rate semantics, sample count, mean/stddev,
quality/accuracy/VRAM/resource regressions, artifact provenance, and current-head
PR-body consistency. Return P0/P1/P2 findings only with concrete missing evidence.
```
