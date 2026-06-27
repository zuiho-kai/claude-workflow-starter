---
name: reviewer-lens-audit
description: Reviewer-perspective audit entrypoint for self-review and read-only sub-agents.
metadata:
  type: feedback
---

# Reviewer Lens Audit

Generic "code check" prompts are weak. They usually answer only whether the patch looks plausible. Reviewer-lens audit makes the review dimensions explicit.

## Avoid These Prompts

- "review this"
- "check if anything is wrong"
- "does this look OK"
- "scan the diff"
- "confirm no issues"

Use the explicit prompt in [reviewer_lens_prompt](reviewer_lens_prompt.md).

## Four Required Audits

1. **Duplication:** Does an existing repo or reference implementation already own this function, class, algorithm, constant, or fixture?
2. **Layering:** Does logic live with the module that owns the data and semantics?
3. **Edge cases:** Are ranges, boundaries, defaults, empty/single/max inputs, and state matrices handled?
4. **Surface area:** Is every new knob, field, schema, or public behavior necessary and fully contracted?

## Upgrade When Needed

- New model, pipeline, backend, or major path: run owner framing in [reviewer_lens_gates](reviewer_lens_gates.md).
- Public API, extra field, processor kwarg, multimodal key, bridge, schema, streaming protocol: write the contract matrix in [reviewer_lens_contracts](reviewer_lens_contracts.md).
- Rebase, cherry-pick, full-diff review, finding closure, inline review: use [reviewer_lens_gates](reviewer_lens_gates.md).

## Finding Format

Each finding must first say:

1. what bad thing can happen;
2. why this change owns it;
3. the smallest acceptable fix.

End with:

```text
AUDITS RUN: 1,2,3,4 — N findings (Pa P0, Pb P1, Pc P2)
```

Sub-agent `OK` is not a test, benchmark, or proof. The main agent still verifies evidence and owns the final call.
