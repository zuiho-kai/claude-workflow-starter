---
name: user_visible_acceptance
description: Acceptance gate for UI, CLI output, public docs, reports, screenshots, visual artifacts, and any behavior a user or reviewer sees directly.
type: feedback
---

# User-Visible Acceptance Gate

Use this whenever a change affects something a user, reviewer, CI reader, or product user will directly see. A green unit test or a successful internal code path is not enough.

## Triggers

- Frontend UI, desktop UI, settings pages, interaction states, animation, screenshots.
- CLI output, error messages, status text, README content, PR bodies, reviewer-facing comments.
- Benchmark, profiling, or accuracy reports; tables; charts; trace summaries; generated artifacts.
- A user or reviewer says they manually saw a problem, could not use the feature, or found the explanation wrong.

## Rules

1. Ordinary user path first.
   Validate through the click, command, config, PR-reading path, or artifact inspection that a real user would use. Do not prove user behavior only through internal strings, direct IPC, mock-only tests, lower-level helpers, or partial DOM presence.

2. The agent is the first QA pass.
   Before handing work back, inspect the current visible output: screenshot, rendered page, CLI output, PR body, benchmark result, trace summary, or artifact.

3. Product shape can block delivery.
   UI overlap, stale styling, unreadable text, wrong state, broken animation lifecycle, misleading report wording, stale head SHA, invalid metric contract, and private detail leakage are blockers even when tests pass.

4. A missed visible bug needs a nearby guard.
   If the user catches a user-visible bug manually, the same fix should add or update the nearest harness, screenshot check, lint/check, manual gate, or repo rule that would catch it next time.

5. Project commands stay project-specific.
   This page defines the framework gate. Concrete commands, artifact paths, and visual-review tools belong in the target project's own docs.

## Template

Before implementation:

```text
User-visible acceptance:
- Ordinary user path:
- Current output/artifact I will inspect:
- Guard to add or update:
- Final command/gate:
```

Before delivery:

```text
I inspected the current user-visible output/artifact: <path or command output>.
The guard that would catch this next time is: <test, harness, check, or manual gate>.
```
