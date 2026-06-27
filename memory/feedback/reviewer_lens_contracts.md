# Reviewer Lens Contracts

Use this when behavior crosses module, request, protocol, or schema boundaries.

## Contract Matrix

Required for new or modified:

- request parameter, `extra_body`, `extra_args`;
- processor kwarg or pipeline extra body;
- multimodal key;
- serving-to-engine, pipeline-to-processor, or cross-module bridge field;
- CLI/example-visible switch;
- public response schema or streaming chunk.

| Column | Required answer |
| --- | --- |
| Ingress | Which top-level field, nested field, CLI, example, or legacy caller can express it? |
| Value shape | How do bool, string bool, `None`, 0/1, sentinel, and missing value behave? |
| Normalization | Which single layer parses and normalizes? |
| Owner | Who owns semantics? |
| Consumer | Which downstream key or field is read? |
| No-op cases | What happens for disabled feature, empty input, or incompatible backend? |
| Docs/tests | Where are docs, schema, bad-path tests, legacy-key tests, and non-default tests? |

Missing any column makes "OK" invalid.

## Streaming / Protocol

Treat streaming, SSE, WebSocket, and OpenAI-compatible chunks as public protocol surface:

- define protocol types in protocol/schema layer;
- reuse existing output processor patterns before hand-rolling delta/error/DONE;
- preserve structured error status/type/code;
- fields named `delta` must be appendable, otherwise expose replacement/snapshot explicitly;
- `[DONE]` is a protocol event, not a finally-block decoration;
- test more than happy-path `200`.
