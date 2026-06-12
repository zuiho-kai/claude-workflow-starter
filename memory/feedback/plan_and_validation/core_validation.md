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

## Performance Evidence Chain

For performance changes, use this chain:

1. Trace symptom.
2. Map stack/source ownership.
3. Make the smallest owner-local change.
4. Validate correctness first.
5. Profile again under the same scope.

Do not report performance from a run whose correctness, metric count, or code path is invalid.
