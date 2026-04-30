# Memory · feedback/

**何时来翻**：每次会话开头扫一眼，避免重犯过的错。`execution_principles.md` + `remote_debug_strategy.md` 是高频，**先读这俩**。

## 协作 / 执行原则
| 文件 | 一句话 |
|------|--------|
| [execution_principles.md](execution_principles.md) | 优先简单方案 / 用 venv / 用户给方案就执行 / 已知结论直接用——4 条合一 |
| [remote_debug_strategy.md](remote_debug_strategy.md) | 远端调试：先侦察、本地试错、不走 git 部署循环、tmux/docker exec 引号陷阱 |
| [auto_push_pr_branches.md](auto_push_pr_branches.md) | PR 分支改完自动 push，不等用户说 |

## 调试方法论 / 接 HF 模型
| 文件 | 一句话 |
|------|--------|
| [feedback_check_official_demo_first.md](feedback_check_official_demo_first.md) | 接 HF 模型做 baseline 必先 grep 官方 README/demo，不要自创参数 |
| [feedback_hf_trust_remote_code.md](feedback_hf_trust_remote_code.md) | trust_remote_code 模型五条教训（读 requirements.txt、不猜版本、查根因） |

## PR / 对齐调试
| 文件 | 一句话 |
|------|--------|
| [feedback_pr_symptom_vs_root_cause.md](feedback_pr_symptom_vs_root_cause.md) | PR "still not fixed" 时先找上游根因；并发场景检查锁的 scope |
| [feedback_pr_test_path_audit.md](feedback_pr_test_path_audit.md) | "已测过的 PR 还有 bug" → 看测试实际跑哪条 path / 断言强度 / 是否被兜底掩盖 |
| [feedback_alignment_debug_pitfalls.md](feedback_alignment_debug_pitfalls.md) | "vllm-omni ↔ HF 对齐"4 个踩坑：multimodal routing、改回滚循环、BF16 笼统归因 |
