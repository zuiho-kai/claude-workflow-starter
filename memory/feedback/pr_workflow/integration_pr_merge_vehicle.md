---
name: integration_pr_merge_vehicle
description: Gate for multi-PR, stacked-PR, and release-candidate workflows: choose one merge vehicle, clear stale status before ready, and close superseded PRs after merge.
type: feedback
---

# Integration PR / Merge Vehicle Gate

Use this when a goal is split across multiple PRs, stacked PRs, release-candidate PRs, evidence PRs, or historical slice PRs. The purpose is to prevent two merge paths from drifting at the same time.

## When To Read

- The same goal has multiple PRs or branches.
- You are creating, readying, or merging an integration/release-candidate PR.
- PR body or docs describe several issues, heads, or validation sets.
- There are superseded PRs, draft PRs, retargeted bases, stacked bases, or merge-order decisions.

## Choose One Merge Vehicle

Before implementation or ready/merge, write:

```text
Primary merge vehicle:
Historical or review-only PRs:
Merge path not chosen:
Integration-only fixes that must not be lost:
```

Rules:

- A related PR set gets one primary merge path.
- If the integration PR is primary, narrow PRs are history or review references.
- If narrow PRs are merged one by one, the integration PR is audit-only unless it is rebuilt from the chosen path.
- A stacked PR whose base is not the target branch is not a final merge vehicle until retargeted, rebased, or absorbed into the integration PR.

## Ready-State Audit

Before changing a draft PR to ready:

```text
PR body stale wording:
Docs stale wording:
Bot/review comments actually ran or were skipped:
Open PR graph and superseded PRs:
CI meaning and what each check executed:
```

Do not mark ready when the body still says draft/WIP, when bot checks were skipped or rate-limited, or when old evidence is written as current-head evidence.

## PR Body Is The Current Contract

An integration PR body should describe current facts:

- current head or merge strategy
- commands and which were run on the current head
- evidence not run and why
- claims that are explicitly not being made
- superseded PR handling when integration is the chosen path

Avoid words like `draft`, `expected`, or `will rerun` after the state has changed. Replace them with actual results or an explicit missing-evidence note.

## New Fix Admission

Classify every new patch before adding it:

| Category | Goes into current PR? | Standard |
| --- | --- | --- |
| Blocker | yes | Without it, user path, CI, merge, or evidence is broken |
| Review finding | usually | Clear P1/P2, small edit, validation is clear |
| Evidence/doc consistency | yes | PR state, docs, body, or check meaning is stale or misleading |
| State-machine polish | default no | Internal neatness only |
| Nice-to-have | no | Can be a separate PR |

Ask:

```text
Would a user fail, misunderstand, or get stuck without this?
Is there a validation gap or clear high-priority finding?
Does the current merge vehicle still stand without it?
```

## Read-Only Reviews Before Merge

For a high-risk integration PR, run read-only reviews before ready/merge:

- code review for behavior bugs, race conditions, and harness false positives/negatives
- merge-readiness review for which PR to merge and in which order
- evidence/docs review for overclaiming, stale wording, and private detail leakage

Sub-agents do not edit public PR text, commit, push, merge, or resolve threads. The main agent verifies their evidence and makes the decision.

## Merge Decision Format

Before merge:

```text
Decision: merge now / merge after X / do not merge yet
Vehicle:
Why this vehicle:
Blockers:
Not a release claim because:
After merge:
```

No decision block, no merge.

## After Merge

After an integration PR merges:

1. Comment on superseded PRs.
2. Close superseded PRs.
3. Confirm the open PR list only contains expected PRs.
4. Run the target-branch checkpoint before making a release claim.

PR-head green is not the same as target-branch or release green.

## Real-Environment Evidence Boundary

Missing real environment evidence may be acceptable for merge, but it blocks release claims. Public docs and PR bodies should state what fake/local harnesses covered, what real environment was not run, and what must happen before release-complete can be claimed.
