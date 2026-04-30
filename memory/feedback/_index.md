# Memory · feedback/

**何时来翻**：每次会话开头扫一眼，避免重犯过的错。`user_prefs.md` 是高频协作偏好，**永远先读**。带 `feedback_` 前缀的是被用户纠正过的具体场景。

## 协作偏好（永远先读）
| 文件 | 一句话 |
|------|--------|
| [user_prefs.md](user_prefs.md) | 用户协作偏好总表 |
| [auto_push_pr_branches.md](auto_push_pr_branches.md) | PR 分支改完自动 push，不等用户说 |

## 调试 / 执行哲学
| 文件 | 一句话 |
|------|--------|
| [feedback_read_memory_before_action.md](feedback_read_memory_before_action.md) | 执行操作前先读相关 memory，不要等出错后再补救 |
| [feedback_no_detours.md](feedback_no_detours.md) | 优先最简单直接的方案，不要绕远路 |
| [feedback_use_venv.md](feedback_use_venv.md) | 远端用 `source .venv/bin/activate`，不要 PYTHONPATH hack |
| [feedback_follow_user_instruction.md](feedback_follow_user_instruction.md) | 用户给出明确方案时直接执行，禁止"先试试不改" |
| [feedback_remote_debug_strategy.md](feedback_remote_debug_strategy.md) | 远端调试不走 git 循环，先在远端快速试错 |
| [feedback_tokenizer_debug_retro.md](feedback_tokenizer_debug_retro.md) | 先侦察再写代码（HF cache 结构 + tokenizer_config 备忘） |
| [feedback_check_official_demo_first.md](feedback_check_official_demo_first.md) | 接 HF 模型做 baseline 必先 grep 官方 README/demo，不要自创参数 |
| [feedback_hf_trust_remote_code.md](feedback_hf_trust_remote_code.md) | trust_remote_code 模型调试五条教训（读 requirements.txt、不猜版本、查根因） |

## PR / 对齐调试
| 文件 | 一句话 |
|------|--------|
| [feedback_pr_symptom_vs_root_cause.md](feedback_pr_symptom_vs_root_cause.md) | PR "still not fixed" 时先找上游根因，并发场景检查锁的 scope |
| [feedback_pr_test_path_audit.md](feedback_pr_test_path_audit.md) | 审计"已测过的 PR 还有 bug"：测试实际跑哪条 path / 断言强度 / 是否被兜底掩盖 |
| [feedback_alignment_debug_pitfalls.md](feedback_alignment_debug_pitfalls.md) | "vllm-omni ↔ HF 对齐"4 个踩坑：multimodal routing、改回滚循环、BF16 笼统归因 |

## Retros（一次性会话总结）
- [retros/feedback_session_retro_2026_04_30.md](retros/feedback_session_retro_2026_04_30.md) — 2026-04-30 HunyuanImage3 对齐会话 9 条踩坑反思
