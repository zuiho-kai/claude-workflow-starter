---
name: Auto Push PR Branches
description: After updating a PR/worktree branch, push automatically once checks pass
type: preference
date: 2026-04-24
---

When working on an existing PR/worktree branch, do not wait for the user to say "push" after finishing a code change.

**Why:** The user explicitly said: "自动push 不要我说".

**How to apply:**
- After implementing a requested PR branch change and passing reasonable local checks, commit or amend as appropriate and push automatically.
- If the branch history was amended, use `git push --force-with-lease`, not a blind force push.
- Keep using DCO sign-off for commits.
- If the user specified an SSH key or remote for the branch, keep using that key/remote for subsequent pushes.
- Only stop before pushing if there is an unresolved test failure, a conflict, missing credentials, or a genuinely risky ambiguity.
