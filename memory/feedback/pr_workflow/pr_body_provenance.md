# PR Body Provenance

Use this before publishing performance, accuracy, metric tables, or output images.

## Evidence Matrix

Draft one row per claim:

```markdown
| ID | Purpose | Input Source | Path | Requests | Key Knobs | Timing Scope | Result | PR Placement |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- |
```

No matrix means no performance / accuracy / image claim.

## Required Binding

For every table or image, know:

- exact command or script;
- input and prompt/request;
- official/user input vs smoke input;
- request count and key knobs;
- timing scope and warmup/init policy;
- metric reference;
- exact conclusion supported.

Smoke evidence must be labeled smoke or compatibility. It cannot be titled accuracy or performance.

## Head / Run / Artifact

PR head, run checkout, metrics, and artifact timestamp/hash should belong to the same run. If not, rerun or label historical evidence explicitly.

Before posting an image, confirm format, size, hash, URL status, and visually inspect that it is the right nonblank artifact.
