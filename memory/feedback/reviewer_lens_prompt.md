# Reviewer Lens Prompt

Use this for a read-only review sub-agent. Do not include your suspected root cause unless the task is explicitly closing an already accepted finding.

```text
Static review this PR/diff/change. For EACH audit below, return findings
(P0 blocker / P1 should-fix / P2 nit) OR explicitly write "none found".
Do not skip any audit and do not pre-focus on one over another.

# Audit 1 — Duplication
Grep the repo and any provided reference implementation for overlapping
functions, classes, algorithms, constants, fixtures, or helpers. For each match,
list existing file:line, new file:line, and reuse judgment.

# Audit 2 — Layering
For each new logic block, identify the module that owns the data and semantics.
Flag logic that lives in an entrypoint, helper, or consumer while the owner is
elsewhere.

# Audit 3 — Edge cases
List ranges, boundaries, defaults, state matrices, empty/single/max inputs,
off-by-one risks, and None/0/sentinel behavior. Flag unhandled branches.

# Audit 4 — Surface area
List every new CLI/API/config/extra field, processor kwarg, schema field,
public response, or optional fast-path parameter. For each, answer whether it is
necessary, where it is normalized, who owns it, who consumes it, how no-op or
unsupported paths behave, and where docs/tests cover it.

For each finding, state:
1. what bad thing can happen;
2. why this change owns it;
3. the smallest acceptable fix.
End with: "AUDITS RUN: 1,2,3,4 — N findings (Pa P0, Pb P1, Pc P2)".
```
