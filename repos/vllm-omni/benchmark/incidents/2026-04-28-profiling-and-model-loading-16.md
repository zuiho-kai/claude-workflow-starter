# 2026-04-28 — pkill -f python 杀死 SSH session

- 编号：`inc-2026-04-28-profiling-and-model-loading-16`
- 归属：`repos/vllm-omni/benchmark`
- 状态：已验证
- 搜索词：pkill -f python 杀死 SSH session
- 影响范围：repos/vllm-omni/benchmark

**症状**：`ssh ... "pkill -9 -f python; ..."` 执行后 SSH 断开，exit code 255
**根因**：`pkill -f python` 匹配所有含 "python" 的进程，包括 SSH session 的子进程
**解法**：用精确 PID kill（`ps aux | grep bench_hf | awk '{print $2}' | xargs kill -9`），或用更精确的 pattern（`pkill -f bench_hf_trace`）
**对未来的提醒**：远端 `pkill -f` 永远不要用 `python` 这种宽泛 pattern，用具体脚本名
