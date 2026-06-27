---
name: code_taste
description: Human-reviewer code taste entrypoint.
type: feedback
---

# Code Taste

Read this before writing code, tests, examples, API fields, CLI flags, or helper functions.

Tests prove that a path ran. They do not prove that the patch is reviewable. Human reviewers catch misleading names, wrong ownership, duplicated helpers, misplaced tests, unexplained strategy, API surface creep, and diff pollution.

## Stop Phrases

Pause if you are thinking:

- "put it here for now"
- "the name is close enough"
- "this test file can import it"
- "copying is fastest"
- "the reviewer will understand"
- "this knob might be useful later"

## Seven Standards

1. **Names describe mechanism.** A name must say what it controls and how, at the right abstraction level.
2. **Logic lives with the owner.** Place behavior with the module that owns the data and semantics, not the nearest editable file.
3. **New helpers start guilty.** Grep the repo, reference implementation, neighboring implementation, and tests before adding one.
4. **Tests live with behavior.** A test file should make its behavior owner obvious.
5. **Tests bind to current diff.** Each new test protects a reviewer comment, current contract, explicit bug, or smallest regression from this fix.
6. **Comments explain strategy.** Explain upstream alignment, invariants, fallback order, and non-obvious boundaries; do not narrate syntax.
7. **Diffs must read cleanly.** File list, naming, comments, test placement, helper reuse, and fallback behavior should survive first-pass review.

## Drill Down

- API fields, config keys, `extra_args`, processor kwargs, protocol schema, bridge fields, optional fast paths, shared state/schema: [code_taste_api_surface](code_taste_api_surface.md).
- New execution paths, diff smell pass, and inline review action mapping: [code_taste_review_flow](code_taste_review_flow.md).
- Push-time reviewer-lens audit or sub-agent review: [reviewer_lens_audit](reviewer_lens_audit.md).

## Owner Hints

- Shared protocol paths preserve user payload semantics; model-specific keys belong to model parsers or pipeline consumers.
- Consumers should not hardcode producer enum values, token ranges, or valid values when the producer can expose them.
- If you need to move data out just to compute behavior, the logic is probably in the wrong place.
- Creating a dedicated owner test file is better than polluting a nearby unrelated test.
