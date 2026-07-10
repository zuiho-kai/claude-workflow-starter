# Agent loop / sub-agent workflow

**何时来翻**：用户明确要求 sub-agent / 并行 agent，或任务能拆成互不依赖的调查面。目标是降低等待和盲区，不是增加流程。

## 是否使用

适合使用：

- 多个代码路径、日志、artifact 或外部来源可以独立核对。
- 高风险 review 需要一个不继承主 agent 结论的只读视角。
- 长任务中有独立的验证、资料整理或兼容性调查可以并行完成。

默认不用：

- 单文件小修、明确 reviewer follow-up、短解释或单条命令。
- scope 尚未收敛，拆分只会复制混乱。
- 多个 agent 会修改同一批文件，或子任务结果必须逐步依赖前一步。

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

## 停止条件

出现以下任一情况就收回主线程判断：

- 证据互相冲突。
- 子任务开始依赖未验证的前置结论。
- 多个 agent 触碰同一写入面。
- 连续尝试没有产生新证据。
- 继续推进需要用户授权或会扩大任务范围。

长跑、远端 GPU、benchmark 的预算和 watchdog 仍由对应场景 runbook 管理，不在这里重复定义。
