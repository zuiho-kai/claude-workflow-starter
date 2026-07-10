# Agent loop / sub-agent workflow

**何时来翻**：用户明确要求 sub-agent / 并行 agent，或任务能拆成互不依赖的调查面。目标是降低等待和盲区，不是增加流程。

## 是否使用

适合使用：

- 多个代码路径、日志、artifact 或外部来源可以独立核对。
- 高风险 review 需要一个不继承主 agent 结论的只读视角。
- 长任务中有独立的验证、资料整理或兼容性调查可以并行完成。
- 非琐碎开发完成后，需要一个没参与实现的 reviewer 做交付前全量审查。

默认不用：

- 单文件小修、明确 reviewer follow-up、短解释或单条命令。
- scope 尚未收敛，拆分只会复制混乱。
- 多个 agent 会修改同一批文件，或子任务结果必须逐步依赖前一步。

上面的“默认不用”只限制实现阶段是否拆分工，不豁免非琐碎开发完成前的独立审查。明确 reviewer follow-up 可以由一个开发 agent 修，但修完仍要由没参与修复的视角复审当前完整改动。

不按文件数、步骤数或模型名称强制开 agent；由任务是否真的可独立决定。

## 最小委派合同

委派只需说明四件事：

1. 目标和范围。
2. 只读还是允许写入；允许写入时独占哪个目录或 worktree。
3. 需要返回的证据，例如文件行号、命令、日志或 artifact。
4. 哪些决定仍由主 agent 保留，例如扩大 scope、公开回复、commit 和 push。

不要把未经验证的 root-cause 猜测写成子任务结论。可以限定对象，不能要求“证明 X 就是原因”。

## 所有权与证据

- 只读 agent 可以共享 checkout；写入 agent 必须隔离目录、worktree 或明确文件所有权。
- 公共 PR body/comment、commit、push、merge 等外部动作只有一个 owner。
- 主 agent 必须复核关键引用；sub-agent 的 `OK` 不能替代测试、live diff、benchmark 或 artifact provenance。
- 子任务发现相邻问题时先作为 out-of-scope note 返回，不顺手扩大当前任务。

## 开发交付的维护者审查闭环

适用于非琐碎的业务代码、测试、公开接口、配置、CLI 或模型适配。目标不是让 reviewer 说句“看起来可以”，而是在交给真实 maintainer 前消掉会阻止合并的问题。

1. 开发 agent 完成实现、目标测试和自审，但此时只能说“待独立审查”。
2. 换一个没参与设计和编码的 reviewer。它只读用户要求、本轮确认的仓库规则、基线和当前完整 diff；不继承作者的根因假设、自审结论或“重点帮我看 X”。
3. reviewer 先分类风险，再按 [全量 diff 审查](../../review/guides/reviewer-lens-gates.md#full-diff-review) 完成改动清点、语义链路和垃圾修改检查，最后审 duplication、layering、edge cases、surface area 和命中的专项路径。每条 finding 必须有等级、文件或函数证据、会坏什么和最小修复。
4. 语气可以像强硬的项目 owner：直接、不放水、不接受假证据；但只评代码和证据，不攻击人。
5. 原开发者在原实现工作区修复 P0/P1/P2；写入 agent 继续遵守已约定的隔离目录、worktree 或文件所有权边界。P2 表示低严重度但仍需修复的实质问题；纯样式 nit 单列且不阻止完成，不能把维护问题降级成 nit。
6. 修复后由 reviewer 重新审查当前完整 diff，既检查旧 finding 是否真正关闭，也查修复引入的新问题。只关闭旧问题不等于全量复审。
7. 只有 reviewer 对当前完整 diff 返回 `0 P0 / 0 P1 / 0 P2` 才能完成。记录首轮 finding、修复轮数、正式测试与环境阻塞；只有存在可靠计时证据时才记录实现和修复耗时，不凭印象估算。

审查 prompt 的通用维度见 [reviewer lens prompt](../../review/guides/reviewer-lens-prompt.md)，如何避免把作者偏见传给 reviewer 见 [review delegation](review-delegation-framing.md)。

当前环境没有独立 agent 能力时，仍要按同一维度做一次新鲜全 diff 自审，并明确报告“未经独立 reviewer”；不能声称已经通过独立维护者审查。

## 停止条件

出现以下任一情况就收回主线程判断：

- 证据互相冲突。
- 子任务开始依赖未验证的前置结论。
- 多个 agent 触碰同一写入面。
- 连续尝试没有产生新证据。
- 继续推进需要用户授权或会扩大任务范围。

长跑、远端 GPU、benchmark 的预算和 watchdog 仍由对应场景 runbook 管理，不在这里重复定义。
