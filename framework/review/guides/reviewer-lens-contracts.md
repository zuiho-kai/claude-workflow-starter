# Reviewer Lens Contracts

Use this when the change exposes, forwards, or normalizes behavior across module boundaries.

## Contract matrix

Required for any new or modified:

- OpenAI-compatible request parameter, `extra_body`, `extra_args`;
- `mm_processor_kwargs`, processor kwarg, pipeline extra body;
- multimodal key such as `image`, `images`, `img2img`;
- AR-to-DiT bridge, serving-to-engine prompt, pipeline-to-processor field;
- CLI/example-visible model behavior switch;
- public response schema or streaming chunk.

| Column | Required answer |
| --- | --- |
| Ingress | Which top-level field, nested `extra_args`, CLI, example, or legacy caller can express the value? |
| Value shape | How do `True`/`False`, `"true"`/`"false"`, `None`, 0/1, sentinel, and missing value behave? |
| Normalization | Which single layer parses and normalizes? Is downstream `bool(value)` forbidden? |
| Owner | Who owns semantics: serving/protocol, AR bridge, DiT pipeline, processor, model config? |
| Consumer | Which downstream key/field is read? Is old key compatibility needed? Is unsupported path fail-fast or documented no-op? |
| No-op cases | What happens for T2I without condition image, disabled feature, empty image list, or incompatible backend? |
| Docs/tests | Where are docs, protocol/schema, bad-path tests, legacy-key tests, and string-bool tests? |

Missing any column makes sub-agent `OK` invalid. Treat as P1 until resolved.

## Audit details

### Duplication

New functions / classes / algorithms / constants require grep across repo and upstream reference:

```bash
grep -rn "<function-name-or-concept>" vllm_omni/ scripts/ <upstream_repo>/
```

Any match needs a one-line reuse judgment. If you cannot explain why not reuse, reuse.

### Layering

Logic belongs with the module that owns the data and semantics:

- entrypoint parsing model-owned data means wrong layer;
- opaque tokens passed downstream usually mean downstream needed raw structure;
- lightweight dependency constraints are solved by moving code to the right heavier layer, not duplicating in lightweight code;
- generic helper names must not leak one caller's private concept.

Question: if you cut/paste the logic into owner module X and it can run directly, it probably belongs there.

### Edge cases

Audit these before claiming clean:

- non-contiguous ID ranges and off-by-one;
- `None` vs 0 vs sentinel;
- empty / single-element / max-size;
- request-local state under batching: tensor shape, non-tensor metadata, request index, CFG branch, slice/offset, KV/attention metadata;
- feature flag x cache mode: cache on/off, prefix hit/miss, last/non-last PP rank, downstream all/subset, staged CPU tensor none/fallback, deferred multimodal keys;
- dormant old code activated by new tests or payload branches;
- fake runner shape vs real wrapper contract: property vs method, CPU/GPU buffer wrapper, `.np`, `copy_to_gpu()`;
- online serving preprocessing, chat template, tokenizer/processor/preprocessor artifacts, request synthesis;
- new model semantic edges: `cos/sin` order, activation, token order, scheduler spacing, `pad_id == eos_id` attention mask, real tokenizer / processor fail-fast.

### Surface area

Default is no new knob. Ask:

- Can the value be derived?
- Is help text explaining too much because the wrong layer owns the default?
- Are multiple knobs mutually exclusive?
- Does an internal optional parameter have a data contract and execution-context contract?
- Does a wrong caller fail at the owner boundary?
- Does backend choice affect correctness?
- Does a shared state/schema change preserve constructor and unpack compatibility?

For shared schema changes, grep all constructors, unpack sites, and consumers. `py_compile` / `ruff` are not enough; execute at least one constructor smoke.

## Streaming / API protocol

Treat `stream`, SSE, WebSocket, and OpenAI-compatible chunks as public protocol surface:

- protocol types live in protocol layer; endpoint code should not yield ad hoc dicts;
- reuse existing endpoint and output processor patterns before hand-rolling delta / error / DONE;
- docs and tests must cover public fields;
- align normal chunk, validation error, `EngineDeadError`, generic exception, client disconnect, and DONE behavior;
- structured errors must preserve status/type/code into error chunks;
- fields named `delta` must be appendable, or the protocol must explicitly say replacement/snapshot;
- `[DONE]` is a protocol event, not a finally-block decoration;
- test more than `200 text/event-stream`: include 4xx preservation, engine-dead/shutdown, and client reconstruction.
