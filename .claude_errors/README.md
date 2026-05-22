# Error Book

踩坑落盘地，按主题分文件（如 `git_and_rebase.md`、`docker_and_container.md`、`ci_and_testing.md`、`remote_and_ssh.md`）。

## 何时写

- 第一次踩到的、未来可能重犯的坑
- Stop hook 提示有错误痕迹时，让 Claude 提议落盘
- 同一坑踩 ≥ 2 次时，从这里升级到 `memory/<topic>.md`（作为常识）
- 同一坑踩 ≥ 3 次或影响范围大时，从 `memory/` 升级到 `CLAUDE.md` 硬规则（**必须标 P1-P7 派生**）

## 格式

按主题追加到 `.claude_errors/<topic>.md`：

```markdown
## YYYY-MM-DD HH:MM — <一句话标题>
**症状**：<报错/不符合预期的具体表现>
**根因**：<分析后的真正原因>
**解法**：<怎么修的>
**对未来的提醒**：<下一次怎么避免>
```

## 主题文件命名

**禁建小文件**。新建主题需三条件齐：
1. 现有主题文件无法容纳
2. 预期复用 ≥ 2 次
3. 是通用主题而非具体 incident（incident 写到对应主题文件内当章节）

命名要**通用化**：`git_and_rebase.md` 不是 `pr_2986_push_failed.md`；`alignment_debug.md` 不是 `model_X_vae_bug.md`。

## 自动化

`skills/claudeception/` 负责数据飞轮自动积累——从会话提炼踩坑记录到这里，条目过多时自动按主题拆分。`stop-gate.sh` hook 在每次 turn 结束检查有无错误痕迹，提醒落盘。

**写入前 Claude 会展示 diff 并请你确认**，不会自动写。
