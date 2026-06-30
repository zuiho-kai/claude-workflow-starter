# PR Body Entry

Read the target repository's PR template before drafting. Match its sections and wording.

## Section Discipline

Keep the target repository's headings unchanged. In repositories that use `Purpose`, `Test Plan`, and `Test Result`:

- `Purpose` is the behavior problem and smallest fix boundary.
- `Test Plan` is the command, script, reproduction path, request construction, or metric method.
- `Test Result` is the actual validation result, metric, artifact, or pass/fail summary.

Do not fill public PR bodies with work logs, old validation SHAs, CI bookkeeping, or local environment blockers unless the reviewer explicitly needs provenance for the claim.

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

Before posting, verify code fences, tables, images, and bullets render correctly. Use a UTF-8 body file rather than fragile shell quoting when possible.

Avoid temporary image hosts and avoid putting fenced Markdown inside shell strings that can strip or corrupt backticks.

After updating a PR body, read it back and check that:

- code fences are still present;
- tables and bullets render as intended;
- images or artifact links are stable;
- no control characters or private paths leaked.

## Evidence Downshift

- Performance / accuracy / image evidence: [pr_body_provenance](pr_body_provenance.md).
- New model evidence split: [pr_body_model_evidence](pr_body_model_evidence.md).
- Privacy boundary: [pr_body_privacy](pr_body_privacy.md).

Acceptance: the PR page reads like a reproducible reviewer report, not a chat log or work diary.
