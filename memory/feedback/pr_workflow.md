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
| Multi-PR, stacked-PR, release-candidate, superseded PR, and merge vehicle decisions | [integration_pr_merge_vehicle.md](pr_workflow/integration_pr_merge_vehicle.md) |

Hard-rule summary:

- Keep the baseline checkout clean when the project uses worktrees.
- Push to the real PR head branch, not a branch invented locally.
- PR evidence must bind to head SHA, run SHA, artifact path, and metric validity.
- PR bodies and comments must stay reviewer-facing; keep private local paths, remote hosts, cache paths, ports, account names, and probe noise out of public text.
- After rebase, cherry-pick, or conflict resolution, run fresh semantic review of conflict files, auto-merged touched files, and current non-outdated review threads.
- Multi-PR or stacked-PR work must choose one merge vehicle. If an integration PR is chosen, narrow PRs become history/review references and should be marked superseded or closed after merge.
- Reviewer follow-up fixes use the smallest credible edit plus targeted validation.
