# Claude Code Workflow Starter

This file is the entrypoint for agents working in this repository. Keep it short: hard gates and routing live here; incident detail belongs in `memory/`, `.claude_errors/`, and `docs/`.

## 0. Start Order

1. Read this file before doing repository work.
2. Before writing code, tests, examples, API fields, CLI flags, or helpers, read [code_taste](memory/feedback/code_taste.md).
3. Before remote, GPU, serving, or benchmark work, read [docs/remote_server.template.md](docs/remote_server.template.md) or your gitignored `docs/remote_server.md`, plus [remote_debug_strategy](memory/feedback/remote_debug_strategy.md).
4. Before new model, new pipeline, new public entrypoint, or performance-claim PR work, read [mini_spec](memory/feedback/mini_spec.md); if model/checkpoint details are involved, also read [model_adaptation_pr_guardrails](memory/feedback/model_adaptation_pr_guardrails.md).
5. Before product parity, roadmap, product-book, or experience-loop planning, read [product_loop_planning](memory/feedback/product_loop_planning.md).
6. Before committing, pushing, rebasing, or opening a PR, re-read the Git / PR rules below. Commits must use DCO sign-off when the target project requires it.
7. Before adding new memory or error-book entries, search [memory/MEMORY.md](memory/MEMORY.md). Append to an existing topic unless the new topic is reusable, general, and cannot fit anywhere else.
8. Repository-specific lessons belong in repository-visible docs such as `memory/`, `.claude_errors/`, or `docs/`, not in a private agent memory store unless the repository explicitly asks for that.

## 1. Principles

- **P1 Evidence first**: no source, grep, or measured evidence means no strong conclusion. Label inference and measurement separately.
- **P2 Simple and direct**: when the user gives a concrete fix, execute it. For equal options, choose the smallest one that satisfies the requirement.
- **P3 Trace the full path**: follow bugs from entrypoint to consumer. Do not fix the most visible function until the owner and downstream effects are clear.
- **P4 One variable at a time**: if two plausible causes remain, narrow them before editing. A multi-change pass is not proof of root cause.
- **P5 Test the real path**: e2e and owner-path tests beat mocks. Syntax checks and compile checks do not prove behavior.
- **P6 No silent fallback**: avoid `dict.get(...) or fallback`, broad `getattr(default)`, `hasattr` probes, and hidden compatibility shims unless the fallback is explicit and logged.
- **P7 Scope discipline**: touch only what the task needs. Move unrelated cleanup into a separate change.
- **P8 Reviewability matters**: names, ownership, reuse, tests, comments, API surface, and diff shape must make sense to a human reviewer.
- **P9 Contract matrix**: for public fields, request keys, config, CLI, schema, or cross-module bridges, list ingress -> normalization -> owner -> consumer -> docs/tests before editing.
- **P10 Public boundary**: public docs and PR text should contain mechanism, commands, versions, and reproducible evidence. Private hosts, local paths, cache paths, internal account details, and exploratory artifacts stay out.
- **P11 Controlled agent loops**: sub-agents and loops are tools for reducing blind spots, not a default ritual. For high-risk work, define objective, scope lock, evidence contract, budget/stop condition, checkpoint handoff, and escalation condition before looping. The main agent owns scope, final judgment, public text, commits, and pushes.
- **P12 User-visible acceptance**: tests passing is not enough for UI, CLI output, public docs, reports, screenshots, or artifacts. Inspect the real user-visible output before handing it back.
- **P13 Product loop first**: for parity, roadmap, product-book, or target-experience work, describe the user-visible loop before splitting technical modules or PRs.
- **P14 Authoring self-review**: when a reviewer or bot finds multiple meaningful issues in your diff, treat it as a missed authoring-time review. Move the lesson into code structure, tests, harnesses, CI gates, or a concrete review gate before the next similar change.

## 2. Hard Gates

### 2.1 Code And Debugging

- State the current assumption before editing. If several explanations are still plausible, narrow first.
- Algorithm decisions must start from upstream or owner code: `modeling_*.py`, `generation_*.py`, tokenizer, scheduler, sampler, parser, or the relevant framework owner.
- A smoke result such as shape-clean, strict-load, no-missing-weights, or no-NaN proves plumbing only. It does not prove semantic parity.
- Crashes and `AttributeError` are trace points, not stop signs. Continue upstream until you know why that path received the wrong type or state.
- If the user rejects the same conclusion twice, treat the user judgment as ground truth and re-check from evidence.
- Use sub-agents only after defining objective, scope lock, evidence contract, budget/stop condition, checkpoint handoff, and escalation condition. If you use a sub-agent, write its delegation prompt first. Small reviewer follow-ups and explicit fast-path requests do not need a full audit loop.
- For product parity, roadmap, or target-experience work, write the ordinary user loop before technical slices: user action, system judgment, persistent state, future trigger, natural expression, user control, and acceptance evidence.
- For UI, CLI output, public explanations, benchmark reports, screenshots, or visual artifacts, define the ordinary user path and inspect the current output/artifact before delivery. See [user_visible_acceptance](memory/feedback/user_visible_acceptance.md).
- Reviewer-facing conclusions should say what breaks, why it matters, and the smallest credible mitigation before internal terminology.

### 2.2 CI, Tests, And Benchmarks

- New or changed tests must run at least once on the target test function or owner path. `compileall`, `ruff`, and `git diff --check` are not semantic validation.
- After editing Python, run `ruff check` on touched files. Before push, also run `ruff format --check --diff` or the project equivalent when available.
- Streaming or protocol changes need bad-path coverage: structured 4xx, engine/runtime failure, appendable deltas, and terminal markers.
- Shared state, batching, cache, runner, or attention metadata changes need a state matrix, not only tensor-shape tests.
- Benchmark plans need a scope lock: measured version, measurement patch, code path, metrics, and invalid-metric rules. Smoke results prove path availability, not performance.
- When a user points to a PR, issue, config, or benchmark spec, anchor that object first: read the actual config, runner/client code, result JSON/artifact, and metric units before answering with numbers.
- Performance results must be classified as `strict apples-to-apples`, `workload-aligned only`, or `smoke only`. Do not turn a workload-aligned or smoke result into a framework performance claim.
- Separate L2 and L4 evidence. L2 tests may cover CPU/mock contracts, shapes, metadata, and errors; L4 covers real weights, accuracy, performance, and profiling. Mock weights do not prove real runtime behavior.
- Reuse existing benchmark, smoke, or offline-inference scripts before writing a new runner.

### 2.3 Remote, Containers, And Long Runs

- Read the remote template or the project-specific `docs/remote_server.md` before remote validation. Treat `user@host:port` as the routing key; do not mix facts across machines.
- Put complex remote commands into scripts. After upload, check byte count, first lines, and syntax before running.
- Services and benchmarks need fail-fast gates: verify nontrivial CLI flags with `--help`, monitor health, PID, and known error signatures, and do a single-request smoke before sweeps.
- New persistent content in containers belongs on a host-mounted path. Reuse complete existing container content read-only; do not install missing dependencies into container layers or root caches.
- For offline model loads, set the project’s offline environment variables or pass a local snapshot path explicitly. Large-model remote runs need a cache preflight: print cache env, disk, GPU, target local path, and a `local_files_only` probe before serving, pytest, generation, or benchmark commands. Existing root cache may be reused read-only only when the snapshot is complete; missing shards or cache misses must fail instead of downloading.
- Profiling requests require trace artifacts, not only benchmark stats. Before delivery, identify the trace files, event coverage, and resource cleanup evidence.
- For graph or compiled profiling, prove the benchmark, trace, request, and server log are from the same run before making graph-mode conclusions.
- Release resources explicitly: kill the process group or project process pattern, exit nested shells, then verify scheduler state and GPU memory.
- On shared machines, keep one control session and low-frequency status reads for long profiling or graph runs.

### 2.4 Git And PR

- Use DCO sign-off (`git commit -s`) when the upstream requires it.
- Keep the main checkout clean as a baseline. Do feature work in a dedicated `wt-<purpose>` worktree when the project uses that pattern.
- Before PR creation and after rebase or cherry-pick, inspect `git log --oneline origin/main..HEAD` and `git diff --stat` for pollution.
- Read the target repo’s PR template before drafting a PR body. Match its sections instead of using a generic format.
- Evidence in PR bodies or comments needs provenance: PR head SHA, run checkout SHA, artifact path, timestamp, and metric validity.
- PR bodies and comments should contain only reviewer-facing evidence. Do not publish local user paths, remote hostnames, cache paths, port numbers, private account names, or internal probe noise.
- Small PRs should list the smallest real command that was run in `Test Plan`; `Test Result` should be a one-line statement of the core behavior covered.
- Multi-PR, stacked-PR, or release-candidate work must choose one merge vehicle before ready/merge. If an integration PR is the vehicle, narrow PRs become history/review references and must be closed or marked superseded after merge. See [integration_pr_merge_vehicle](memory/feedback/pr_workflow/integration_pr_merge_vehicle.md).
- Before pushing nontrivial code or tests, run a reviewer-lens audit: classify risk tags, select the needed lenses, then check duplication, layering, edge cases, and surface area. Fix findings or document why not.
- After rebase, cherry-pick, or conflict resolution, run a fresh semantic review of conflict files, auto-merged touched files, and current non-outdated review threads.
- Reviewer follow-up fixes can use a fast path: confirm finding -> minimal edit -> targeted test or blocker note -> lint touched files -> signed commit -> push.
- Sub-agents must stay read-only unless the main agent explicitly assigns a local implementation task. They must not edit public PR bodies/comments, commit, push, merge, or resolve review threads.

### 2.5 Architecture And Package Management

- Avoid adding JSON/YAML launch config unless the project explicitly owns config that way. Prefer CLI or existing registry conventions.
- Remote package installs should use the project’s pinned package manager and cache roots; make cache and venv locations explicit.
- On Windows or PowerShell, read/write text as UTF-8 explicitly when editing shared docs.

## 3. Routing Index

- Main memory index: [memory/MEMORY.md](memory/MEMORY.md)
- Code taste: [memory/feedback/code_taste.md](memory/feedback/code_taste.md)
- Execution principles: [memory/feedback/execution_principles.md](memory/feedback/execution_principles.md)
- Plan and validation: [memory/feedback/plan_and_validation.md](memory/feedback/plan_and_validation.md)
- PR workflow: [memory/feedback/pr_workflow.md](memory/feedback/pr_workflow.md)
- Reviewer lens: [memory/feedback/reviewer_lens_audit.md](memory/feedback/reviewer_lens_audit.md)
- Agent loop workflow: [memory/feedback/agent_loop_workflow.md](memory/feedback/agent_loop_workflow.md)
- User-visible acceptance: [memory/feedback/user_visible_acceptance.md](memory/feedback/user_visible_acceptance.md)
- Product loop planning: [memory/feedback/product_loop_planning.md](memory/feedback/product_loop_planning.md)
- Model adaptation PR guardrails: [memory/feedback/model_adaptation_pr_guardrails.md](memory/feedback/model_adaptation_pr_guardrails.md)
- Upstream-first algorithm checks: [memory/feedback/upstream_first_for_algorithm.md](memory/feedback/upstream_first_for_algorithm.md)
- Remote debugging: [memory/feedback/remote_debug_strategy.md](memory/feedback/remote_debug_strategy.md)
- Container setup: [memory/remote/container_setup.md](memory/remote/container_setup.md)
- Remote lifecycle: [memory/remote/srun_lifecycle.md](memory/remote/srun_lifecycle.md)
- Error book: [.claude_errors/README.md](.claude_errors/README.md)
- Architecture template: [docs/architecture.md](docs/architecture.md)
- Remote server template: [docs/remote_server.template.md](docs/remote_server.template.md)
