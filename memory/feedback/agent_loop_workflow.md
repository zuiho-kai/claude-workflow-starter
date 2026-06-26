# Agent loop / sub-agent workflow

**何时来翻**：用户提 loop agent / sub-agent / 多智能体，或任务属于 benchmark、远端验证、CI failure、reviewer 争议、PR body 证据修复、scope audit。目标不是把所有任务自动化，而是决定什么时候值得用额外视角，什么时候必须走 fast path。

## 1. 核心判断

Sub-agent 的优势不是更聪明，而是角色隔离：

- main agent 容易一边查、一边改、一边解释，最后自己说服自己。
- sub-agent 适合独立查代码、日志、测试、artifact、PR body 风险，降低盲区。
- sub-agent 不适合最终拍板，因为它只有局部任务上下文，不一定知道用户真实 scope、PR 历史、公开口径和哪些信息不能写出去。

默认规则：main agent 负责判断和交付，sub-agent 负责只读调查。公开动作只有一个出口：main agent。

## 2. 什么时候不用

不要为了显得像 loop engineering 而开循环。以下场景默认不用 sub-agent：

- 小 reviewer follow-up，用户已经说清楚 `just fix it` / “小改一下”。
- 单文件小 bug，复现路径和目标测试都明确。
- 用户要的是短解释、paste-ready reply、或一个明确命令。
- scope 还没锁，sub-agent 会先继承混乱目标。
- 多个 agent 会同时改同一批文件。

这些场景走 fast path：确认 live diff / reviewer note，最小修改，跑目标验证，必要时 push。

## 3. 什么时候值得用

以下场景可以开 1-3 个只读 sub-agent，但先写 scope lock：

- 代码 review：用 reviewer 视角查 layering、edge case、测试位置、surface area。
- Benchmark / remote validation：独立核对 config -> runner -> payload -> server log -> result JSON -> PR body。
- PR body / public comment：检查是否 overclaim、泄漏内部路径/host/cache、或把探索 run 写成可发布证据。
- Stale review thread：对比历史评论、当前 live diff、当前 PR body，确认评论是否仍成立。
- 大范围路径调查：并行查多个 owner/path，但最终由 main agent 合并判断。

## 4. 每种场景的收益和代价

| 场景 | sub-agent 优点 | sub-agent 缺点 |
| --- | --- | --- |
| 小 reviewer fix | 基本没有收益 | 浪费 token，容易把小事搞成 full audit |
| 代码 review | 独立挑 layering、edge case、测试位置 | 上下文不全，误报多 |
| Benchmark / remote validation | 可以拆链路核对，减少 main agent 漏看 payload/log/artifact | 容易只看局部证据，下错整体结论 |
| PR body / public comment | 能发现 overclaim、隐私泄漏、证据不够 | 不适合最终定公开口径 |
| Stale review thread | 能独立确认历史评论是否还匹配 live diff | 如果没明确要求看 live diff，也会跟着旧评论跑偏 |
| 大范围代码路径调查 | 并行找 owner/path，节省主上下文 | 结果碎片化，必须主 agent 重新整合 |

## 5. Loop 开跑前必须写清

任何 loop / sub-agent 前，main agent 必须先写清：

- Objective：这轮到底要完成什么。
- Scope lock：哪些文件、PR、workload、metric、reviewer note 属于范围；哪些明确不属于。
- Evidence contract：什么证据才算有效，例如测试命令、server log、result JSON、artifact mtime/hash、live diff。
- Stop condition：什么时候停，不继续扩。
- Escalation condition：什么时候必须问用户，而不是继续猜。

没有这些，就不要开 loop。

## 6. Sub-agent 输出格式

Sub-agent 只交证据，不交最终决定：

```text
Finding:
Evidence:
Confidence:
Missing proof:
Recommended owner action:
Out-of-scope notes:
```

要求证据写具体文件、行号、日志片段、命令或 artifact 路径。禁止只写 “looks good” / “seems fine”。

## 7. Main agent 收口规则

main agent 必须做这几件事：

- 复核 sub-agent 引用的文件、日志或 artifact。
- 把“技术上可能存在的问题”和“当前 PR 必须处理的问题”分开。
- 对 benchmark / PR body，只采用满足 evidence contract 的结果。
- 对 public comment / PR body，删掉内部路径、临时失败、远端 host/cache、个人账号和工作流水账。
- 如果 sub-agent 发现相邻问题，先判断是否 scope expansion；不是当前 scope 就记为 follow-up，不顺手改。

## 8. 禁止事项

- 禁止让 sub-agent 自己改公开 PR body/comment。
- 禁止让 sub-agent commit、push、merge、resolve review thread。
- 禁止把 sub-agent 的 `OK` 当测试或 benchmark 通过。
- 禁止把探索 run、失败 run、半冷 run 写成 reviewer-facing evidence。
- 禁止因为开了 sub-agent 就扩大任务范围。
- 禁止在用户要求 fast path 时强行开 full audit。
