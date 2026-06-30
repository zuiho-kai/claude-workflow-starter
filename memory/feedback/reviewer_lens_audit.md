---
name: reviewer-lens-audit
description: Reviewer-perspective audit entrypoint for self-review and read-only sub-agents.
metadata:
  type: feedback
---

# Reviewer Lens Audit

Generic "code check" prompts are weak. They usually answer only whether the patch looks plausible. Reviewer-lens audit makes the review dimensions explicit.

## Classify First

Do not start by hunting bugs. First classify what kind of system property changed, then choose the lenses.

Minimum classification:

```text
Review risk tags:
- public API / user-facing contract:
- module semantic contract:
- cross-module producer-consumer contract:
- async / concurrency / scheduling:
- resource lifetime / cleanup:
- data format / serialization / IPC:
- performance claim / benchmark evidence:
- error handling / cancellation / timeout:
- feature flag / config / default behavior:
- backward compatibility:
- test or validation evidence:
Selected lenses:
```

If you did not write risk tags and selected lenses, call the result a partial review.

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
- Async, concurrency, scheduler, IPC, shared resource, resource lifetime, GPU/CPU transfer, or performance claim: add a systems/runtime lens and, when evidence is involved, an evidence/benchmark lens.
- Rebase, cherry-pick, full-diff review, finding closure, inline review: use [reviewer_lens_gates](reviewer_lens_gates.md).
- If a reviewer or bot finds multiple meaningful issues after you authored the diff, treat that as an authoring-time self-review miss. Add a gate, test, harness, or code-structure change for the next similar diff.

## Finding Format

Each finding must first say:

1. what bad thing can happen;
2. why this change owns it;
3. the smallest acceptable fix.

End with:

```text
AUDITS RUN: 1,2,3,4 — N findings (Pa P0, Pb P1, Pc P2)
```

Sub-agent `OK` is not a test, benchmark, or proof. The main agent still verifies evidence, unions findings, and owns the final call.
