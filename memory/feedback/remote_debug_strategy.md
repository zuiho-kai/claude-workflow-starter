---
name: Remote debugging strategy routing
description: Route remote reconnaissance, fail-fast serving, cleanup, profiling, and benchmark validation.
type: feedback
---

# Remote Debug Strategy Entry

This file is only a router. Remote tasks should open the matching topic first.

| Scenario | Read this |
| --- | --- |
| New machine or environment reconnaissance, cache checks, tmux/SSH command shape | [basics.md](remote_debug_strategy/basics.md) |
| Serving or benchmark startup gates, watchdogs, cleanup, ownership of failures | [serving_failfast_cleanup.md](remote_debug_strategy/serving_failfast_cleanup.md) |
| Graph/profiling runs on shared machines, profiler config, trace quality | [profiling.md](remote_debug_strategy/profiling.md) |

Hard-rule summary:

- Git commit-push-pull is deployment, not debugging.
- Complex remote commands should become scripts with byte-count, preview, and syntax checks.
- Serving and benchmark runs need fail-fast gates before sweeps.
- Shared-machine profiling uses one control session and low-frequency status reads.
