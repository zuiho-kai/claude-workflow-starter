# Branch, Push, And Rebase

## Mechanism Entry

Read this page in two layers:

- General mechanism: confirm git root/worktree, task type, true PR head branch, DCO/sign-off requirements, push remote, and rebase semantic review.
- Private operation details: fork aliases, SSH host aliases, concrete identities, historical PR numbers, and account-specific remotes belong in private runbooks. Public synchronization should keep only the rule: push with the PR owner's required identity and writable remote; never invent a branch name.

Fixed order:

1. Decide whether this is a new PR, an existing PR follow-up, or a rebase/cherry-pick update.
2. For an existing PR, discover the true head owner and branch before pushing.
3. Before editing, verify whether the project expects a dedicated worktree.
4. Commit with the required sign-off/trailer policy.
5. Push through the writable remote or SSH identity required by the PR owner.
6. After rebase, cherry-pick, or automatic conflict resolution, treat conflict files and shared paths as a fresh diff and run semantic review again.

## Worktree Boundary

When a project uses a clean baseline checkout, do not write feature changes there. Create or use a dedicated worktree named for the task, then verify the git root before editing.

## Before Push

Run:

```bash
git status --short --branch
git log --oneline origin/main..HEAD
git diff --stat origin/main...HEAD
```

Look for:

- unrelated files
- accidental local settings
- generated artifacts
- old debug probes
- commits with unclear scope

## Push Target

Check the actual PR head branch and owner before pushing. For fork PRs, push to the fork branch that backs the PR. Use the project-specific SSH identity only when the project rules require it.

## Rebase Or Cherry-Pick

After conflict resolution, rerun the log/stat audit and a semantic audit of conflict files. A conflict-free rebase can still silently keep stale behavior.

## Existing PR Follow-Up Fast Path

Use the fast path only when the finding is already clear, the edit is small, no public API or cross-owner behavior is added, and the touched files stay within the current finding.

1. Confirm the remote PR head.
2. Make the minimal edit.
3. Run the targeted test or record the blocker.
4. Lint/format touched files according to project rules.
5. Commit with sign-off and push.

Do not run a full PR scope process for a tiny reviewer follow-up unless the fix expands owner boundaries or touches new public surface.
