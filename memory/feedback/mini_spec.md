# Mini Spec

Use this before non-trivial model, pipeline, public entrypoint, execution-path, performance-claim, or docs/config work.

The mini spec is short. Its job is to make "done" verifiable before code starts.

## Triggers

- New model, pipeline, backend, or public entrypoint.
- New step, graph, cache, batching, serving, offline, or benchmark path.
- New or changed public API, CLI, extra field, processor kwarg, multimodal key, bridge field, or response schema.
- Scheduler, decode, latent, cache, batch, or protocol semantics.
- Performance, accuracy, or public docs claim.

## Template

```text
Goal:
Changed surfaces:
Field contract:
  ingress:
  default semantics:
  owner:
  consumers:
  failure policy:
Path parity matrix:
  normal path:
  variant paths:
  shared helper or intentional split:
Validation:
  local:
  remote/e2e:
  benchmark/profiling:
Public evidence:
Explicit non-goals:
```

If this cannot be written in a few lines, the scope is not understood yet. If it seems too heavy, the change should be simple enough to summarize even more briefly.
