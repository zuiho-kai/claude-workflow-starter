---
name: Plan 阶段 trace 完整 lifecycle / 功能验证默认 e2e / 性能优化证据链
description: 写 plan 时不要拿单点快照建模——必须 grep 全调用链；用户问"feature 能不能用"默认 e2e smoke，不要给刚写的函数堆 FakeXxx 单元测试；性能优化按 trace 现象→stack/source→ownership→小 PR→profiling/accuracy 验证推进
type: feedback
---

# Plan / Validation 入口

本文件只保留路由。日常先按任务类型打开对应专题页；不要整篇读历史 runbook。

| 任务 | 读这个 |
|------|--------|
| 写 plan、判断 feature 是否可用、选择 e2e vs fake/unit、性能优化证据链 | [core_validation.md](plan_and_validation/core_validation.md) |
| benchmark 口径、探索/smoke/sweep 区分、scope lock、结果命名 | [benchmark_scope.md](plan_and_validation/benchmark_scope.md) |
| 远端长测配置验证、复用既有脚本、profiler 不污染 steady-state | [remote_long_run.md](plan_and_validation/remote_long_run.md) |
| AR graph / profiling 诊断机制、d-step 分析、PR 远端验证闸门；Hunyuan 具体复跑参数下沉到 archive | [hunyuan_ar_runbooks.md](plan_and_validation/hunyuan_ar_runbooks.md) |
| 新模型 / execution path / public 字段 / multimodal payload / perf PR 开发前 mini spec | [reviewer_lens_audit.md](reviewer_lens_audit.md) 的“开发前 mini spec” |

硬规则摘要：

- Plan 阶段先 trace lifecycle，再给方案。
- 功能验证默认打真实 e2e 路径；fake/unit 不能证明全栈可用。
- Benchmark 先锁被测版本、测量补丁、被测路径、有效指标。
- 用户给出 PR 或“这个规格”时，先读该 PR/config/runner/result JSON 锁 source of truth，再回答或开跑。
- L2/L4 拆分先定义证据边界：L2 CPU/mock 功能 shape guard，L4 真实权重 accuracy/perf/profiling。
- 已有成功脚本或 runbook 时先复用，禁止从零手写等价 runner。
- 非平凡模型适配、execution path、public 字段或 perf PR，开发前先写 mini spec；不能把后续 review 当第一道语义检查。
