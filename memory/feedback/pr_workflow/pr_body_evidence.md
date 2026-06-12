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

## Rendered Check

Before posting, check that tables, code fences, images, and bullet lists render correctly. A technically correct PR body that renders badly still costs reviewer time.
