# Memory · feedback/

**何时来翻**：先按 `CLAUDE.md` 判断任务场景；只有被场景路由到 feedback 时才读本索引。不要每次会话默认读完整 feedback，也不要把远端调试规则带进 docs-only / PR-body / 小解释任务。

## 协作 / 执行原则
| 文件 | 一句话 |
|------|--------|
| [execution_principles.md](execution_principles.md) | 简单方案优先 / 用户给方案直接执行 / 已知结论直接用——执行类合集 |
| [plan_and_validation.md](plan_and_validation.md) | plan 先 trace lifecycle；功能验证默认 e2e；benchmark/spec 先锁 source of truth；公开同步只保留机制层 |
| [pr_workflow.md](pr_workflow.md) | worktree / push / PR body / reviewer follow-up / rebase fresh review 的提交前路由 |
| [remote_debug_strategy.md](remote_debug_strategy.md) | 远端调试：侦察、fail-fast cleanup、profiling 状态机、trace quality gate |
| [mini_spec.md](mini_spec.md) | 非平凡模型 / pipeline / public entrypoint / execution path / perf claim / docs-config 变更前的 canonical mini spec |
| [model_adaptation_pr_guardrails.md](model_adaptation_pr_guardrails.md) | 新模型 / 新 pipeline / 新 public entrypoint / 性能 claim PR 的 mini spec、checkpoint、entrypoint、evidence gate |
| [agent_loop_workflow.md](agent_loop_workflow.md) | loop / sub-agent 使用门禁：scope lock、evidence contract、stop condition、main-agent 收口 |
| [user_visible_acceptance.md](user_visible_acceptance.md) | 用户可见输出验收门禁：UI / CLI / PR body / 报告 / artifact 必须走普通用户路径并检查当前输出 |

## 调试方法论 / 接 HF 模型
| 文件 | 一句话 |
|------|--------|
| [feedback_hf_trust_remote_code.md](feedback_hf_trust_remote_code.md) | trust_remote_code 模型踩坑：读 requirements.txt、不猜版本、查根因、改 snapshot 不改 cache |
| [systematic_vs_stochastic_divergence.md](systematic_vs_stochastic_divergence.md) | "路径 A 一直 X，路径 B 一直 Y" 是 systematic 不是 stochastic；PIL mode RGBA→RGB 是 silent bug 源 |

## PR / 对齐调试
| 文件 | 一句话 |
|------|--------|
| [feedback_pr_symptom_vs_root_cause.md](feedback_pr_symptom_vs_root_cause.md) | PR "still not fixed" 时先找上游根因；并发场景检查锁的 scope |

## Review / Sub-agent / 代码品味
| 文件 | 一句话 |
|------|--------|
| [code_taste.md](code_taste.md) | **写代码前必读**：人工 reviewer 代码品味短入口；API surface 见 [code_taste_api_surface.md](code_taste_api_surface.md)，execution path / diff smell / inline review 见 [code_taste_review_flow.md](code_taste_review_flow.md) |
| [reviewer_lens_audit.md](reviewer_lens_audit.md) | 自审 + sub-agent review 的短入口；prompt、gates、contracts、cases 已拆到 reviewer_lens_* 小页 |
| [review_delegation_framing.md](review_delegation_framing.md) | spawn review sub-agent 时禁传自己 hypothesis；要么开放式 audit 要么并行多 framing union |
| [agent_loop_workflow.md](agent_loop_workflow.md) | sub-agent 只交证据；公开动作、commit、push、review thread 由 main agent 收口 |
| [user_visible_acceptance.md](user_visible_acceptance.md) | 用户或 reviewer 能直接看到的行为，不能只靠内部测试证明；必须检查真实输出或 artifact |

## 调试收敛 / 结论纪律
| 文件 | 一句话 |
|------|--------|
| [conclusion_discipline.md](conclusion_discipline.md) | invariant=bug detector / harmless 必须有完整因果链 / 推理 vs 实测前缀 / 用户 ≥2 次反驳必翻盘 |
| [debug_funnel_discipline.md](debug_funnel_discipline.md) | 调试漏斗：grep 优先 / 收敛到 1 个怀疑再动手 / user 给诊断 ≠ 给修法（B32 来源）|
| [upstream_first_for_algorithm.md](upstream_first_for_algorithm.md) | algorithm 决策前先 grep upstream 源码（B30 来源）|
| [algorithm_vs_framework_fix.md](algorithm_vs_framework_fix.md) | 同现象 framework hack vs algorithm fix 时 default to algorithm fix（B31 来源）|

## 任务拆解 / 范围纪律
| 文件 | 一句话 |
|------|--------|
| [task_as_audit_enumeration.md](task_as_audit_enumeration.md) | TaskCreate 列枚举步骤不是修复目标；sub-agent action list 不能直接当 ground truth（B23 来源）|
| [narrow_optimization_scope.md](narrow_optimization_scope.md) | 调试中"顺手优化"分类：主线必需带，周边收益延后独立 PR（F8 来源）|
