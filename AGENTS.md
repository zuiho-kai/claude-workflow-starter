# Agent Instructions

Before doing any work in this repository, read `CLAUDE.md` and follow it as the source of truth.

For git commits and PR branch pushes, re-read the git-related rules in `CLAUDE.md` first. Commits must include DCO sign-off (`-s`).

If your project uses multiple GitHub identities (e.g., personal + org), configure them via SSH host aliases in `~/.ssh/config` and push with the right host alias:

```bash
git push git@github-<alias>:<org>/<repo>.git HEAD:<branch>
```

Don't accidentally push with the wrong identity—org PR branches usually need the org's SSH key, not your personal HTTPS credentials.
