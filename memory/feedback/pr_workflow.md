---
name: PR workflow routing
description: Route branch hygiene, PR testing, PR body evidence, reviewer follow-up, and scope narrowing.
type: feedback
---

# PR Workflow Entry

This file is only a router. Before commit, push, PR body work, or reviewer follow-up, open the matching topic.

| Scenario | Read this |
| --- | --- |
| Main/worktree boundary, PR head owner/branch, push target, rebase/cherry-pick audits | [branch_push_rebase.md](pr_workflow/branch_push_rebase.md) |
| "Still not fixed", already-tested bugs, official-reference tests | [debugging_and_tests.md](pr_workflow/debugging_and_tests.md) |
| PR template, rendered body checks, artifact and metric provenance | [pr_body_evidence.md](pr_workflow/pr_body_evidence.md) |
| Reviewer asks to shrink scope, remove dead route, or avoid diff pollution | [scope_narrowing.md](pr_workflow/scope_narrowing.md) |

Hard-rule summary:

- Keep the baseline checkout clean when the project uses worktrees.
- Push to the real PR head branch, not a branch invented locally.
- PR evidence must bind to head SHA, run SHA, artifact path, and metric validity.
- Reviewer follow-up fixes use the smallest credible edit plus targeted validation.
