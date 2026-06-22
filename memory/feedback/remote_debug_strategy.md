---
name: 远端调试策略：先侦察、本地试错、不走 git 部署循环
description: 2026-04-21 HunyuanImage3 tokenizer 修复用 6 轮 git commit-push-pull 才跑通，烧一天+$300。教训：调试 ≠ 部署、先侦察再写代码、tmux/docker exec 引号陷阱
type: feedback
---

# Remote Debug Strategy 入口

本文件只保留路由。远端任务先按场景打开专题页，避免一次性载入全部 graph/profiling 复盘。

| 场景 | 读这个 |
|------|--------|
| 新机器/新模型侦察、HF cache、tmux/docker exec、减少 SSH 次数、issue 复现 | [basics.md](remote_debug_strategy/basics.md) |
| serving/benchmark 启动 gate、watchdog、cleanup、pytest/accuracy 归属清理 | [serving_failfast_cleanup.md](remote_debug_strategy/serving_failfast_cleanup.md) |
| AR graph serve、comprehension gate、profiler config、trace quality、online start/stop | [ar_graph_profiling.md](remote_debug_strategy/ar_graph_profiling.md) |
| full pipeline benchmark connector/指标 gate、AR graph tail-gap 诊断 | [full_pipeline_benchmark.md](remote_debug_strategy/full_pipeline_benchmark.md) |

硬规则摘要：

- git commit-push-pull 是部署手段，不是调试手段。
- 远端复杂命令先落脚本，检查 `wc -c`、前 40 行和 `bash -n`。
- serving/benchmark 必须先 fail-fast，单请求 smoke 通过前不进 sweep。
- 共享机器 graph/profiling 用一个控制会话和低频状态文件，不要密集 SSH 轮询。
