---
name: CI gitignore blocks JSON files
description: vllm-omni .gitignore 有 *.json 规则，新增 JSON test config 必须 git add -f
type: project
originSessionId: e9b427d0-9d70-4f38-a8ed-3e53f47f593e
---
vllm-omni 的 `.gitignore` line 241 有 `*.json`，会忽略所有 JSON 文件。

**Why:** 项目里有大量生成的 JSON（benchmark results 等），所以全局忽略。但 `tests/dfx/perf/tests/*.json` 是手写的 test config，需要被 track。

**How to apply:** 新增 JSON test config 文件时必须 `git add -f <file>` 强制添加，否则 git status 不会显示为 untracked，容易漏提交。
