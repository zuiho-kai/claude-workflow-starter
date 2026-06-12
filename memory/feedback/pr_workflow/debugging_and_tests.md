# PR Debugging And Tests

## "Still Not Fixed"

When a reviewer or user says a PR is still broken:

1. Reproduce or trace the exact path they mean.
2. Identify whether the patch touched the owner or only a downstream symptom.
3. Check adjacent paths that share the same public contract.
4. Add or update the smallest test that protects the owner behavior.

Do not add a defensive patch to an unrelated layer just because it makes one smoke pass.

## Already-Tested Bugs

If a bug survives tests, ask what the tests did not cover:

- wrong entrypoint
- fake object instead of owner path
- happy path only
- missing bad-path assertion
- stale fixture
- test checks input shape, not final behavior

Update the test at the behavior owner.

## Official Reference Tests

When a test claims parity with an official or upstream implementation, load the reference from the real upstream snapshot or package. Importing the project’s own copied implementation is not a reference.
