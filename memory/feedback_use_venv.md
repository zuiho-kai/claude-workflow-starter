---
name: Use source .venv not PYTHONPATH
description: 远端环境用 source .venv/bin/activate 而不是 PYTHONPATH hack
type: feedback
originSessionId: 9a1ebfe4-abd5-4132-9a19-bf213b2b4cc4
---
远端需要 vllm 0.19 时，直接 `source <YOUR_REMOTE_WORKDIR>/.venv/bin/activate`，不要用 PYTHONPATH 指向 .venv/lib/... 的 hack。

**Why:** 用户明确说过 "你为什么就是不肯用source .venv呢"。PYTHONPATH 方式不可靠（优先级问题、遗漏依赖），而且绕远路。
**How to apply:** 远端跑 vllm-omni 相关命令前，第一步永远是 `source <YOUR_REMOTE_WORKDIR>/.venv/bin/activate`。
