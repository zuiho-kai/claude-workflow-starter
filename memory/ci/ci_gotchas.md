---
name: CI 配置常见坑——gitignore / pipeline config / perf 测试隔离
description: .gitignore 排了文件类型时新增配置文件必须 git add -f；单阶段 pipeline 要关 async_chunk；perf 测试 OOM 应拆成独立 CI step + soft_fail
metadata:
  type: project
---

# CI 配置常见坑

## 1. .gitignore 排某类文件，新增配置文件必须 git add -f

项目的 `.gitignore` 可能全局忽略某些类型（如 `*.json`），会忽略手写的 test config。

**Why:** 项目里有大量生成的 JSON（benchmark results 等），所以全局忽略。但 `tests/dfx/perf/tests/*.json` 这类是手写的 test config，需要被 track。

**How to apply:** 新增被 `.gitignore` 覆盖的 test config 文件时必须 `git add -f <file>` 强制添加，否则 `git status` 不会显示为 untracked，容易漏提交。

**检查方法：** `git check-ignore -v <file>` 验证某文件是否被 gitignore 拦截。

## 2. 单阶段 pipeline 必须关 async_chunk

单阶段 pipeline（只有一个处理阶段，没有 next-stage）启动时必须禁用 `async_chunk`。

**Why:** `async_chunk` 默认 `True`（或类似设置）。单阶段 pipeline 没有 next-stage processor，`async_chunk=True` 直接报 `ValueError` 或类似错误。

**How to apply:**
- 永久修法：在 deploy/pipeline config 里写 `async_chunk: false`（或等价设置）
- 临时修法：启动命令加 `--no-async-chunk`（或等价 flag）
- 判断依据：单阶段 pipeline（只有一个处理器，没有 producer→consumer bridge）= 必须关 `async_chunk`

## 3. 大模型 perf test 在 CI 多 case 同 session 里会 OOM

perf test 多个 parametrized case 在同一 pytest session 里连跑，前一个 server 没杀干净就起下一个，显存叠加爆了。

**Why:** EXIT5 或 OOM 传播到后续 step 的 exit code，导致整个 mandatory step 失败。

**How to apply:**
- 把大模型 perf test 从 mandatory CI 拆成独立 step，加 `soft_fail: true` + env gate（`RUN_PERF=1` 等，默认不跑）
- 每个 parametrized test case 对应独立 pytest 调用，只起一个 server，防止显存残留
- CI 节点 HF cache 里要有对应模型；如果有 base/Instruct 两个版本，确认 CI 节点有哪个
