# Agent Loop And Sub-Agent Workflow

Use this when a task mentions loop agents, sub-agents, multi-agent review, or when the work has high risk: benchmarks, remote validation, CI failures, reviewer disputes, PR body evidence, stale review threads, or scope audits.

The goal is not to automate every task. The goal is to decide when an extra isolated view reduces blind spots and when the fast path is the better engineering move.

## Core Rule

Sub-agents are useful because they isolate roles:

- The main agent can accidentally investigate, edit, explain, and convince itself in one pass.
- A sub-agent can independently inspect code, logs, tests, artifacts, PR wording, and risk.
- A sub-agent usually lacks full user intent, live scope, public/private boundaries, and project history.

Default ownership:

- Main agent owns scope, judgment, final answer, public text, commits, pushes, and review-thread actions.
- Sub-agents provide read-only evidence unless explicitly assigned a contained local implementation task.

## When Not To Use A Loop

Do not run a loop just to look thorough.

Default to a fast path for:

- small reviewer follow-ups
- single-file bugs with a clear owner and target test
- user requests for a short explanation, paste-ready reply, or exact command
- tasks where the user has said "just fix it" or equivalent
- cases where scope is not locked yet
- cases where multiple agents would edit the same files concurrently

Fast path means: confirm the live diff or reviewer note, make the minimal change, run targeted validation or state the blocker, and stop.

## When A Sub-Agent Helps

Use one to three read-only sub-agents when the task benefits from independent evidence:

| Scenario | Useful Check | Risk |
| --- | --- | --- |
| Code review | layering, edge cases, test ownership, public surface | false positives from missing context |
| Benchmark or remote validation | config -> runner -> payload -> server log -> result JSON -> PR text | local evidence may be overgeneralized |
| PR body or public comment | overclaim, missing provenance, private detail leakage | public wording still needs main-agent judgment |
| Stale review thread | old comment vs live diff vs current PR body | old comments can steer the task off scope |
| Large path investigation | parallel owner/path discovery | fragmented results need synthesis |

## Pre-Loop Contract

Before starting a loop, write:

```text
Objective:
Scope lock:
Evidence contract:
Stop condition:
Escalation condition:
```

If those fields cannot be filled in, do not start the loop.

Examples of evidence contracts:

- code review: file and line references plus owner-path reasoning
- benchmark: command, checkout, workload, result JSON, server log, metric contract
- PR text: current PR head, public workload, reproducible command, private-detail scan
- remote validation: host category, cwd, venv, cache env, GPU allocation, logs, artifact path

## Sub-Agent Output Format

Require evidence, not vibes:

```text
Finding:
Evidence:
Confidence:
Missing proof:
Recommended owner action:
Out-of-scope notes:
```

Avoid prompts that ask only "review this" or "does this look okay". Ask for concrete checks, and require `none found` when a category has no finding.

## Main-Agent Closeout

The main agent must:

- verify cited files, logs, commands, and artifacts
- separate "technically possible issue" from "must fix in this scope"
- apply only evidence that satisfies the contract
- remove private hosts, local paths, cache roots, account names, and exploratory noise from public text
- keep adjacent findings as follow-ups unless the user expands scope

## Prohibited Uses

- Do not let sub-agents edit public PR bodies or comments.
- Do not let sub-agents commit, push, merge, resolve review threads, or label issues.
- Do not treat a sub-agent `OK` as a passing test, benchmark, or proof.
- Do not turn exploratory, failed, partial, or semi-cold runs into reviewer-facing evidence.
- Do not expand scope just because a sub-agent found an adjacent issue.
- Do not force a full audit loop when the user asked for a fast path.
