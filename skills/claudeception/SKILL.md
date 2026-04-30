---
name: claudeception
description: |
  落盘项目经验和教训反思——把会话里的踩坑写到 .claude_errors/，常识写到 memory/。
  触发：/claudeception 命令、用户说"记到 error book / 加到 memory"、调试 >10 分钟、反复试错的任务结束后。
  不生成新 skill。展示 diff 给用户确认后再写。
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - AskUserQuestion
---

# Claudeception — 落盘项目经验 + 教训反思

踩坑 → `.claude_errors/<topic>.md` 追加；常识 → `memory/<subdir>/<topic>.md`。先 grep 重复，再展示 diff，确认后再写。

## memory subdir 路由

| 关键字 | subdir |
|--------|--------|
| SSH / Slurm / docker / 容器 / Lustre / tmux / 远端环境变量 | `remote/` |
| HF / HuggingFace / baseline / prompt / tokenizer | `hf/` |
| CI / pytest / fixture / accuracy test / `tests/` | `ci/` |
| 用户偏好 / 用户纠正 / 调试方法论 | `feedback/` |
| 项目快照 / 不再活跃的模型考古 | `archive/<project>/` |

不确定就问用户，禁止凭感觉新开 subdir。

## 格式

**Error book**（追加）：
```markdown
## YYYY-MM-DD — <标题>
**症状**：… **根因**：… **解法**：… **对未来的提醒**：…
```

**Memory**：
```markdown
---
name: <标题>
description: <一句话摘要，具体到能判断相关性>
type: feedback | project | reference | rule
---
<内容>

**Why:** … **How to apply:** …
```

## 写完必做

1. `memory/<subdir>/_index.md` 加一行（钩子 + 链接）
2. 新开 subdir 才动 `memory/MEMORY.md`，已有的不碰
3. 同一坑 `.claude_errors/` 出现 ≥2 次 → 提醒升级到 `CLAUDE.md` 硬规则，附两次日期
4. 单文件 >10 条或 >2000 字 → 按主题拆 `<file>_<subtopic>.md`，原文件留索引

## 不要

- 生成新 SKILL.md
- 重复写已有内容
- 记显然事实 / 一次性事件
- 留密码 / IP / 用户名（用 placeholder）
