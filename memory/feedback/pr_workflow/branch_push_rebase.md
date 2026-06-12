# Branch, Push, And Rebase

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
