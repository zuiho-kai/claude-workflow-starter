# Agent Instructions

Before doing any work in this repository, read `CLAUDE.md` and follow it as the source of truth.

For git commits and PR branch pushes, re-read the git-related rules in `CLAUDE.md` first. Commits must include DCO sign-off.

When pushing updates to PR branches owned by `TaffyOfficial`, use the Taffy SSH identity:

```bash
git push git@github-taffy:TaffyOfficial/<repo>.git HEAD:<branch>
```

The `github-taffy` SSH host is configured in `~/.ssh/config` with `IdentityFile ~/.ssh/id_taffy`. Do not use the default HTTPS GitHub identity for Taffy-owned PR branches.
