---
name: claudeception
description: |
  数据飞轮自动积累系统：从工作会话中提炼踩坑记录和常识知识，自动写入 .claude_errors/（error book）
  和 memory/（常识 book），并在单文件条目过多时自动按主题拆分归类。
  触发条件：(1) /claudeception 命令回顾本次会话 (2) 踩坑后说"记到 error book" (3) 发现非显然知识
  (4) 任何涉及调试、workaround、反复试错的任务完成后。
  不生成新 skill，只积累 error book 和 memory。
author: Claude Code
version: 4.0.0
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - AskUserQuestion
---

# Claudeception — 数据飞轮自动积累

从工作会话中提炼知识，自动写入 error book 和 memory。不生成新 skill。

## 输出目标

| 知识类型 | 写到哪 | 格式 |
|---------|--------|------|
| 踩坑（报错、走弯路、非预期行为） | `.claude_errors/<topic>.md` | Error Book 格式 |
| 常识（通用模式、环境知识、协作偏好） | `memory/<topic>.md` | Memory frontmatter 格式 |

## 触发条件

以下任一情况出现时，自动执行提炼：

1. 用户调用 `/claudeception`
2. 用户说"记到 error book"、"加到 memory"、"记住这个"
3. 调试花了 >10 分钟才解决的问题
4. 报错信息和真正根因不一致（误导性报错）
5. 试了多种方案才找到正确的（反复试错）
6. 发现项目/环境特有的非显然知识

## 分类判断

问自己两个问题：

1. **这是一个"坑"吗？**（报错了、走弯路了、浪费时间了）→ 写 `.claude_errors/`
2. **这是一个"知识"吗？**（环境配置、版本兼容、命名约定、协作偏好）→ 写 `memory/`

如果两者都是（踩坑过程中发现了通用知识），两边都写。

## Error Book 格式

追加到 `.claude_errors/<topic>.md`：

```markdown
## YYYY-MM-DD HH:MM — <一句话标题>
**症状**：<报错/不符合预期的具体表现>
**根因**：<分析后的真正原因>
**解法**：<怎么修的>
**对未来的提醒**：<下一次怎么避免>
```

`<topic>` 按主题归类（如 `git_and_rebase.md`、`docker_and_container.md`、`model_loading.md`）。

## Memory 格式

新建或追加到 `memory/<topic>.md`：

```markdown
---
name: <标题>
description: <一句话摘要——要具体到能判断相关性>
type: feedback | project | reference
---

<内容>

**Why:** <为什么这条知识重要>
**How to apply:** <什么场景下用、怎么用>
```

type 分类：
- `feedback`：协作偏好、调试策略、工作流改进
- `project`：项目特有的技术决策、配置、状态
- `reference`：跨项目通用的技术知识

## 写入后必做

1. **更新 CLAUDE.md 索引**：如果新建了 memory 文件，在 CLAUDE.md 的"项目记忆"表里加一行
2. **检查升级条件**：如果同一个坑在 `.claude_errors/` 里出现 ≥2 次，提醒用户升级到 CLAUDE.md 硬规则区

## 自动拆分归类

当单个文件条目过多时自动拆分：

### Error Book 拆分（`.claude_errors/` 单文件 >10 条）
1. 读取文件所有 `## YYYY-MM-DD` 条目
2. 按主题聚类（git 相关、docker 相关、模型加载相关、远端调试相关...）
3. 拆成多个文件：`<原文件名>_<subtopic>.md`
4. 原文件保留为索引，列出拆分后的文件链接

### Memory 拆分（`memory/` 总文件数 >25 或单文件 >2000 字）
1. 检查是否有多个主题混在一个文件里
2. 按主题拆分成独立文件
3. 更新 CLAUDE.md 索引表

## 回顾模式（/claudeception）

会话结束前调用时：

1. 回顾本次会话的完整上下文
2. 识别所有可提炼的知识点（踩坑 + 常识）
3. 逐条分类并写入对应文件
4. 检查是否需要拆分归类
5. 报告：写了几条到哪些文件

## 质量标准

写入前确认：
- [ ] 内容是非显然的（不是文档里直接能查到的）
- [ ] 内容是已验证的（实际发生过，不是猜测）
- [ ] 内容是可复用的（下次遇到同样情况能用上）
- [ ] 没有包含敏感信息（密码、IP、用户名用 placeholder）
- [ ] 格式符合 Error Book / Memory 模板

## 不要做的事

- **不要生成新的 SKILL.md 文件**——知识写到 error book 和 memory
- **不要重复已有内容**——先 grep 检查是否已记录
- **不要记录显而易见的事**——"pip install 能装包"不值得记
- **不要记录一次性的事**——只记可复用的模式
