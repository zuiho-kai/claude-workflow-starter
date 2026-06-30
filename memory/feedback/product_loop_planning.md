---
name: product-loop-planning
description: Plan product parity, roadmap, product-book, and target-experience work from user-visible loops before technical modules.
type: feedback
---

# Product Loop Planning

Use this when the request is about parity with another product, a target experience, a product book, a roadmap, or a version goal.

The first artifact should be a user-visible product loop, not a technical module list. A checklist of internal parts can all test green while the user still cannot feel the promised experience.

## Loop First

Before splitting issues, PRs, or sub-agents, answer:

1. What does the user naturally do?
2. What does the system decide in the background?
3. What persistent state is saved, changed, or deleted?
4. What future user action or environment event triggers the behavior again?
5. How does the system express the result in product language?
6. How can the user inspect, correct, disable, or delete it?
7. Which harness, benchmark, artifact, or manual path proves the loop rather than only one helper?

Only after this loop is clear should the work be split.

## Atomic Issue Test

An atomic issue must close a user-visible slice of the loop. It can be small, but it cannot be only "add a layer", "create a type", or "implement an algorithm".

Each issue should state:

- user-visible result;
- current product gap;
- loop start and loop end for this slice;
- explicit non-goals;
- acceptance evidence;
- follow-up loop dependency.

## PR And Sub-Agent Check

Before opening PRs or assigning sub-agents:

- If the plan is only a module list, rewrite it around the loop.
- If several issues only cover internal parts of the same loop, combine them or create an integration slice.
- If one PR starts filling a neighboring loop, split that work out.
- If a benchmark passes but the user experience is still absent, add a loop-level scenario.

Acceptance: the plan reads like a product behavior path a user can feel, verify, and control.
