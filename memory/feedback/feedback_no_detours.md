---
name: Don't take unnecessary detours
description: 不要绕远路，优先用最简单直接的方案
type: feedback
---

遇到环境问题时，优先用最简单直接的方案，不要绕远路。

**Why:** 用户明确指出过：比如 venv 已经有正确版本的包，直接激活 venv 就行，不要去折腾 pip install 升级系统包、加别名 patch 等复杂方案。
**How to apply:** 先检查现有环境（venv、conda 等）是否已经有需要的东西，有就直接用。不要在有简单方案时选择复杂方案。
