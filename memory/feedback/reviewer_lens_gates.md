# Reviewer Lens Gates

## Mini Spec Appendix

Before non-trivial work, write the canonical [mini_spec](mini_spec.md). Reviewer-lens can add review details, but it cannot replace the mini spec.

Appendix fields:

```text
Changed surfaces:
Field contract:
Path parity matrix:
Non-default tests:
Validation and PR evidence:
Explicit non-goals:
```

## Design Review Before Implementation

For runner, cache, shared execution state, pipeline, public API, batching, streaming, or multi-module ownership changes, run owner framing before choosing a patch shape:

- module owner: contracts, data boundary, edge cases, tests, simplest acceptable implementation;
- project owner: repo fit, public/internal surface, docs/evidence, validation matrix.

Pure typo, formatting, and non-behavior docs edits can skip this gate.

## Fix Closure Is Not Full Review

After fixing a finding, review the new diff:

```text
Prior findings resolved?
Any new API/test/docs/PR-body surface?
Return P0/P1/P2 or no further findings.
```

## Full Diff Review

For full PR review or "is this too big / polluted", collect:

```bash
git diff --stat origin/main...HEAD
git diff --name-status origin/main...HEAD
git diff --numstat origin/main...HEAD
```

Run diff census, semantic trace to public consumers, and garbage pass for duplicate logic, silent fallback, unused knobs, docs/perf overclaim, and helper-only tests.

## Rebase / Cherry-Pick Gate

After rebase, cherry-pick, or conflict resolution, old reviews are stale. Re-check conflict files, auto-merged touched files, and current non-outdated review threads. Lint does not replace semantic review.

## Inline Review Mapping

Before editing an inline review comment:

```text
Comment:
Anchor:
Pronoun target:
Reviewer asks:
Code action:
Done check:
```

Anchor code is source of truth.
