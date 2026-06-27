# PR Body Entry

Read the target repository's PR template before drafting. Match its sections and wording.

## Public Reproduction

For e2e, accuracy, performance, or artifact claims, the PR body should contain only public or repo-relative information:

- command or repo-relative script;
- relevant config path and key fields;
- request construction;
- metric calculation;
- public reference or stable artifact URL;
- pass/fail or measured result.

Private machine, cwd, venv, host, port, account, cache, and scratch details belong in private notes, not public PR text. See [pr_body_privacy](pr_body_privacy.md).

## Render Gate

Before posting, verify code fences, tables, images, and bullets render correctly. Use a body file rather than fragile shell quoting when possible.

## Evidence Downshift

- Performance / accuracy / image evidence: [pr_body_provenance](pr_body_provenance.md).
- New model evidence split: [pr_body_model_evidence](pr_body_model_evidence.md).
- Privacy boundary: [pr_body_privacy](pr_body_privacy.md).

Acceptance: the PR page reads like a reproducible reviewer report, not a chat log or work diary.
