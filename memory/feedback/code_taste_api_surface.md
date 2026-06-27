# Code Taste · API Surface

Use this before adding public or semi-public knobs, request fields, optional fast paths, or shared schema fields.

## New Knobs Default To No

Before adding a CLI arg, API field, config key, or `extra_args` key, answer:

- Can the value be derived from existing inputs?
- Will its default conflict with another path's default?
- Does the user need to control it directly?
- Does downstream already have a more stable raw expression?
- Can it ever be removed?

If the answer is vague, do not add the knob.

## Contract Matrix

For request fields, nested extra fields, processor kwargs, multimodal keys, protocol schemas, and cross-module bridge fields, write:

- **ingress:** top-level field, nested field, CLI/example, legacy caller;
- **value shape:** bool, string bool, `None`, 0/1, sentinel, omitted;
- **normalization:** the single parse point; downstream should not re-parse with `bool(value)`;
- **owner:** protocol, serving, bridge, pipeline, processor, model config;
- **consumer:** actual downstream key/field, legacy compatibility, unsupported path behavior;
- **no-op:** empty input, disabled feature, unsupported backend;
- **docs/tests:** docs, bad-path, string-bool, legacy-key, non-default tests.

Prefer raw facts over premature internal concepts.

## Internal Optional Parameters

Adding a function parameter is API surface. Document:

- creator and consumer;
- device, dtype, shape, contiguity, and lifetime;
- rank, stage, mode, stream, or cache-enabled context;
- `None` semantics;
- where a wrong caller fails.

Data contracts belong at the data owner. Execution-context contracts belong at the caller owner that knows the runtime context.

## Shared State Or Schema

Changing a dataclass, `NamedTuple`, `TypedDict`, msgspec Struct, or request/response schema is a shared ABI change. Grep constructors, positional calls, unpack sites, and consumers. Add fields at the end with defaults, or convert constructors to keyword calls.

`py_compile` and lint do not prove runtime arity compatibility. Execute at least one constructor or serialization smoke.
