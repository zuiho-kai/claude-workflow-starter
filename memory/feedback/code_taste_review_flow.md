# Code Taste · Review Flow

Use this for new execution paths, push-time diff review, and human inline review handling.

## New Execution Paths

Trigger when adding step-wise, graph, cache, batching, serving, offline, benchmark, or any second path for existing behavior.

Rules:

- Do not duplicate parsing, normalization, or validation from the normal path.
- Put request parsing in the data owner helper; both paths call it.
- Name return values by consumer, not by vague normalized value.
- Diverge only at explicitly unsupported capability boundaries, and fail fast or no-op visibly.
- Test one default and one non-default field. Default-only tests do not prove parity.

## Diff Smell Pass

Before commit or push:

```bash
git diff --stat origin/main...
git diff origin/main... -- <changed-files>
```

Check for off-scope files, copy-like helpers, names needing oral explanation, misplaced tests, strategy-free comments, accidental public surface, missing docstrings/contracts, wrong-owner runtime guards, shared schema arity risk, and silent fallback.

## Human Reviewer Simulation

Each new logic block must answer:

- Why here?
- Why this name?
- Why not reuse?
- Why this test and this file?
- Why this default?
- Which edge case owns this branch?
- Which upstream or official behavior matches it?
- What happens when a future caller passes a wrong optional parameter?
- Is this a shared state/schema change?

If not, redesign before coding.

## Inline Review Action Mapping

Reviewer anchor lines are source of truth. Before editing an inline comment:

```text
Comment:
Anchor:
Pronoun target:
Reviewer asks:
Code action:
Done check:
```

Do not fix by keyword alone. If the anchor logic remains in the questioned owner, the comment is not resolved.
