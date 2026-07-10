# Remote Debug Strategy 入口

本文件只保留路由。远端任务先按场景打开专题页，避免一次性载入全部 graph/profiling 复盘。

| 场景 | 读这个 |
|------|--------|
| 新机器/新模型侦察、HF cache、tmux/docker exec、减少 SSH 次数、issue 复现 | [basics.md](../../../../framework/remote/guides/debug-basics.md) |
| serving/benchmark 启动 gate、watchdog、cleanup、pytest/accuracy 归属清理 | [serving_failfast_cleanup.md](../../../../framework/remote/guides/serving-failfast-cleanup.md) |
| AR graph serve、comprehension gate、profiler config、trace quality、online start/stop | [ar_graph_profiling.md](../../benchmark/guides/ar-graph-profiling.md) |
| full pipeline benchmark connector/指标 gate、AR graph tail-gap 诊断 | [full pipeline benchmark](../../benchmark/guides/full-pipeline-benchmark.md) |

硬规则摘要：

- git commit-push-pull 是部署手段，不是调试手段。
- 远端复杂命令先落脚本，检查 `wc -c`、前 40 行和 `bash -n`。
- serving/benchmark 必须先 fail-fast，单请求 smoke 通过前不进 sweep。
- 共享机器 graph/profiling 用一个控制会话和低频状态文件，不要密集 SSH 轮询。
