# Agent Instructions

Before doing any work, read `CLAUDE.md`. It is the repository-neutral routing and safety entrypoint.

Then follow one routing order:

- Choose the matching general topic from the map in `CLAUDE.md` and read its `framework/<topic>/_index.md`.
- Identify the repository that actually owns the task from `repos/_index.md`.
- If that repository is registered, read its `_index.md` and any linked `rules.md` before changing code, running remote jobs, benchmarking, committing, or pushing.
- Never apply one repository's rules, machine paths, credentials, remotes, or model assumptions to another repository.

Before adding or moving knowledge, read `CONTRIBUTING.md`, update the nearest `_index.md`, and run `python tools/check_knowledge_tree.py`.

Before committing or pushing, follow the target repository's own Git and identity rules. Do not inherit a commit identity, SSH host, remote, DCO requirement, or PR format from an unrelated repository entry.
