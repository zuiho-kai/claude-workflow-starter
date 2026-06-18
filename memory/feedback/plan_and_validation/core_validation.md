# Core Validation

## Plan Before Editing

Before a plan becomes implementation, trace the real lifecycle:

- entrypoint and user input shape
- normalization and validation
- owner module
- downstream consumer
- error handling and output shape
- existing tests or scripts that already touch the path

If two plausible owners remain, do not pick by convenience. Grep both, state the ownership argument, and choose the smaller owner-correct edit.

## E2E By Default

When the user asks whether a feature works, default to a real path smoke:

- real entrypoint or closest existing example
- real parser/processor/runner path
- real output validation
- targeted failure path when behavior is protocol-facing

Fake objects are useful after ownership is established, but they cannot prove that the feature works end to end.

## L2 / L4 Evidence Split

Before splitting a test plan into lightweight and heavyweight tiers, define the evidence boundary:

- L2: CPU/mock functional contract, request schema, batching semantics, shape, dtype, metadata, and error behavior.
- L2 forbidden path: real model load, runner or stage initialization, CUDA device initialization, remote cache dependency, or real checkpoint download.
- L4: real-weight accuracy, performance, profiling, memory, and artifact-backed results.

Mock weights do not automatically make a test L2. If the test initializes the real runner, stage, device, or external cache path, it is no longer a lightweight functional guard.

When reporting L2, say what it covers and what it does not cover. Do not let mock success read like accuracy or performance coverage.

## Performance Evidence Chain

For performance changes, use this chain:

1. Trace symptom.
2. Map stack/source ownership.
3. Make the smallest owner-local change.
4. Validate correctness first.
5. Profile again under the same scope.

Do not report performance from a run whose correctness, metric count, or code path is invalid.

## Repository Memory Placement

When a repository task asks to "record", "land", "remember", or "write up" a reusable lesson, prefer repository-visible locations:

- `CLAUDE.md` for short hard gates
- `memory/` for reusable runbooks and guidance
- `.claude_errors/` for failure patterns and postmortems
- `docs/` for user-facing handoff material

Private agent memory may be useful for personal recall, but it is not a substitute for repository-visible rules when future collaborators need to find the lesson with `git grep`.
