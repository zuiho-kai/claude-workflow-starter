---
name: model_adaptation_pr_guardrails
description: Pre-work gates for new model, pipeline, backend, public entrypoint, and performance-claim PRs.
type: feedback
---

# Model Adaptation PR Guardrails

Use this when a change adds or exposes a model, pipeline, backend, public path, serving endpoint, recipe, supported-model entry, or performance claim.

Hard rule: write a short mini spec before implementation. Unit tests, shape checks, and strict weight loading are useful plumbing evidence, but they do not prove public entrypoints, semantic parity, or performance.

## Mini Spec

Keep it short, but cover every field:

```text
Mini spec
- Goal:
- Checkpoint layout:
  - runnable model id:
  - upstream/raw model id, if different:
  - required files/subfolders:
- Public entrypoints:
  - offline:
  - serving:
  - recipe/docs:
  - perf config:
- Request fields:
  - ingress:
  - default semantics:
  - owner:
  - consumers:
  - failure policy:
- Path parity:
  - normal path:
  - variant path:
  - shared helper or intentional split:
- Validation tiers:
  - unit:
  - public smoke:
  - formal perf:
- PR evidence:
  - latest-head:
  - historical:
  - pending:
- Non-goals:
```

If the mini spec cannot be written in a few concrete lines, the change is not a small patch.

## Checkpoint Layout

Before writing a model id into public docs, examples, recipes, or perf configs, verify the loader can consume that layout.

Check:

- model index or equivalent registry metadata
- required subfolder configs for transformer, VAE, scheduler, tokenizer, processor, or text encoder
- whether the loader supports raw checkpoint files, Diffusers-style folders, adapters, or split components
- whether the upstream model id and runnable model id are actually the same layout

Public runnable commands should use the checkpoint that the current loader can load. Raw upstream checkpoints belong in notes or references until the loader supports them.

## Public Entrypoint Matrix

For each public path, prove the required command shape and required fields:

| Path | Must Prove |
| --- | --- |
| offline generation | model id, class or registry selection, sampling fields, output handling |
| image/video/reference input | multimodal key, single/multi input policy, latents or image path |
| serving endpoint | endpoint, form/body fields, model id, required params |
| performance config | workload, mode, runner support, and metric fields |
| recipe/docs | command matches a path that has either run or is clearly marked pending |

Do not put a text-only command under an image/video recipe as if it validated reference input. If a live serving smoke did not run, say it is pending.

## Request Parsing And Path Parity

Adding a second execution path does not justify copying request parsing.

Common second paths:

- text-to-output vs reference-input generation
- offline vs serving
- direct args vs prompt dict or nested extra fields
- normal forward vs step, graph, cache, batch, or benchmark path
- image tensors vs precomputed latents or embeddings

Rules:

- Shared request semantics belong in one owner helper.
- Helper outputs should be named by consumer. Do not reuse one normalized value for different meanings.
- Unsupported paths should fail fast or be documented no-ops, not silent skips.
- Tests must include at least one non-default field. Default-only smoke does not prove parsing parity.

Precomputed tensor-like fields should be all-or-none across a batch. If one request supplies an embedding or attention-mask field, either every relevant request supplies it or the code fails fast with the missing index. Do not use Python `or` or truthiness to merge tensor-like values.

## Validation Tiers And PR Wording

Keep PR evidence separated:

```text
Latest-head validation:
- command, checkout, version, and result for the current head

Historical reference:
- older checkout or artifact, labeled as historical

Pending:
- remote GPU, cache, serving smoke, formal perf, or CI still required
```

Performance claims require a formal sweep with matching version, workload, result JSON, and logs. Endpoint exploration, single-request smoke, unit tests, and shape checks cannot be presented as speedups.

Public PR text should include reproducible commands, public versions, commit SHAs, and pass/fail outcomes. Keep private local paths, remote hosts, cache details, private account names, and exploratory failure noise out of public text.

## Public Performance Numbers

Docs and recipes should not publish latency, memory, warmup, throughput, or quality numbers without provenance.

Allowed:

- instructions to run a benchmark before publishing numbers
- hardware-class guidance that is clearly not a measurement
- historical tables with checkout, environment, workload, and metric fields

Not allowed:

- copying numbers from private notes without provenance
- writing pending formal perf in the PR but presenting validated results in docs
- using a small smoke workload to imply a larger documented workload is validated

## Full Diff Review Gate

Before a nontrivial model or pipeline PR is pushed or described as clean, run a full diff review, not only closure of known comments.

Start with:

```powershell
git diff --stat origin/main...HEAD
git diff --name-status origin/main...HEAD
git diff --numstat origin/main...HEAD
```

Then review:

1. Top changed files by size and owner.
2. Every helper, parser, default, scheduler, processor, or bridge through its public consumer.
3. Tests for owner-path coverage rather than helper-only coverage.
4. Docs, recipes, and perf configs for runnable model ids, workload match, and evidence wording.

Report:

```text
DIFF REVIEW BASE: <base>...<head>
TOP FILES REVIEWED: <files>
AUDITS RUN: diff-census, semantic-trace, garbage-pass, reviewer-lens-1..4
```

If only known review comments were checked, say `known findings closed`; do not say `full PR reviewed` or `clean`.

## Reviewer Loop

For complex model adaptation, a one-pass "review this" prompt is weak. Use a question-first loop:

```text
You are a fresh low-context reviewer.
First response must be QUESTIONS ROUND 1.
Ask 3-6 concrete questions with file:line evidence, what is unclear, and what answer would change the review.
Stop after questions.
After answers, validate against code.
Only produce final P0/P1/P2 findings after FINALIZE_REVIEW.
```

Answers should point to file lines, commands, or artifacts the reviewer can verify. Treat "no evidence" as a real finding until evidence exists or wording is reduced.
