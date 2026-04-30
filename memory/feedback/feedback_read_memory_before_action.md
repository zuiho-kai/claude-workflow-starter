---
name: Read relevant memory before taking action
description: 执行操作前必须先读相关 memory，不要等出错后再补救
type: feedback
---

在执行任何操作前，如果该操作涉及已有 memory 覆盖的主题，**必须先读取相关 memory 文件**。

**Why:** Memory 系统存在的目的是避免重复踩坑。如果等到操作失败后再读 memory，就浪费了时间和资源（远端调试成本高）。用户已经在之前的会话中总结了最佳实践，我应该直接应用，而不是重新试错。

**How to apply:**

1. **触发条件** — 用户请求涉及以下主题时，先读 memory 再行动：
   - 远端 SSH / Slurm / 容器操作 → `memory/ssh_*.md`, `memory/remote_*.md`, `.claude_errors/remote_*.md`
   - Git 操作（commit / rebase / worktree）→ `.claude_errors/git_*.md`
   - CI 测试 / 新增测试 → `memory/ci_*.md`, `memory/always_inspect_existing_tests_first.md`
   - 新模型接入 / 调试 → `memory/feedback_tokenizer_debug_retro.md`（先侦察）
   - 容器环境变量 → `memory/transformers_cache_gotcha.md`, `memory/hf_hub_cache_gotcha.md`

2. **读取顺序**：
   - 先读 `memory/MEMORY.md` 索引，找到相关主题
   - 读取对应的 memory 文件
   - 读取对应的 error book（`.claude_errors/`）
   - 然后再执行操作

3. **判断标准**：
   - 如果我在操作失败后说"抱歉，我没有读取这个 memory"，说明我违反了这条规则
   - 正确的流程是：读 memory → 按 memory 里的方案执行 → 成功（或遇到新问题时更新 memory）

**违反记录：**
- 2026-04-27：用户要求 SSH 到远端，我直接尝试 SSH 而没有先读 `memory/ssh_windows_strategy.md`，导致用户质问"为什么会不阅读"
