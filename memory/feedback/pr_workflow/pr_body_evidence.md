# PR Body Evidence

## Template First

Read the target repository's PR template before drafting. Match the repository's sections and wording.

## Provenance Gate

Every performance, accuracy, image, or artifact claim should include:

- PR head SHA
- run checkout SHA
- command or script
- artifact path
- artifact timestamp or hash when relevant
- run count and input scope
- invalid or unavailable metrics

If any of these do not match, label the evidence as exploratory or rerun.

## Public Boundary

PR bodies and comments should contain reviewer-facing evidence only:

- behavior changed
- public command or test command
- dependency versions when relevant
- commit SHA or public run identifier
- pass/fail result
- metric class and validity

Keep these out of public PR text:

- local user paths
- remote hostnames, usernames, ports, or machine aliases
- venv, cache, model-cache, or scratch paths
- private account names or credential details
- local dependency blockers that do not affect reviewers
- exploratory probe noise and failed private attempts

Private debugging context can guide the fix, but it should be summarized into reproducible public evidence before posting.

## Small PR Shape

For small bugfix or reviewer-follow-up PRs:

- `Test Plan` should name the smallest real command that actually ran.
- `Test Result` should be one sentence describing the core regression behavior covered by that command.
- hygiene checks such as formatting, `compileall`, or `git diff --check` can be run privately, but they do not replace semantic validation.

Only list individual test functions when reviewers need a case-by-case mapping. Otherwise prefer the file-level or target command that was run.

## Rendered Check

Before posting, check that tables, code fences, images, and bullet lists render correctly. A technically correct PR body that renders badly still costs reviewer time.
