# Scope Narrowing

Reviewer follow-up is not a chance to refactor surrounding code.

## Keep

- the exact bug fix or requested behavior
- the test tied to that behavior
- minimal docs needed for public API changes

## Remove Or Defer

- defensive patches for unrelated models or owners
- cleanup found while debugging
- tests that only protect a discarded route
- helper abstractions with a single caller and no clear local pattern

## Diff Gate

Before commit, every changed file should answer:

- Which user request or reviewer finding requires this file?
- What test or validation binds to it?
- Could this be a separate PR?

If the answer is weak, remove or defer the file.
