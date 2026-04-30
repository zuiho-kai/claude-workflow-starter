---
name: feedback_pr_symptom_vs_root_cause
description: 诊断"PR 没修好"时，先问是症状修复还是根因修复；环境变量并发场景要检查锁的 scope
type: feedback
---

当 reviewer 说 PR "still doesn't fix the issue"，不要继续在同一层面加 fallback，要往上找：

1. **确认失败场景**：PR 已有的 fallback 在哪个输入组合下仍然失败？
2. **找上游状态来源**：该函数收到的"错误输入"是谁设置的？是调用方竞态还是配置错误？
3. **检查锁的 scope**：`threading.Lock()` 在类/函数内创建 → per-instance；在模块顶层创建 → shared。并发场景下 per-instance 锁对跨实例的共享资源（如 `os.environ`）没有任何保护。

**Why:** PR #3207 只修了 `_map_device_list` 的映射逻辑（symptom），没发现真正的根因是 `_initialize_stages` 里的锁是 per-instance 的，导致多引擎并发时 `CUDA_VISIBLE_DEVICES` 被污染，才传入了"错误的" visible 列表。

**How to apply:** 看到"环境变量读-改-还原"模式 + 多实例并发，立刻检查锁是模块级还是实例级。
