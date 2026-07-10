# Workflow Starter 开工入口

本文件只负责三件事：告诉 agent 先读哪里、哪些通用风险必须硬停、长期知识应该写到哪里。仓库、代码模块、模型和机器专属规则不写在这里。

## 0. 开工顺序

1. 确认用户正在操作哪个真实仓库；不要用当前 shell 路径或历史对话猜。
2. 从下面的知识地图选择一个匹配的 `framework/<主题>/_index.md`，只读取当前任务需要的通用方法。
3. 从 [仓库列表](repos/_index.md) 找当前仓库。只要仓库已经登记，就必须读取 `repos/<仓库>/_index.md`、它链接的 `rules.md`，以及与当前任务同名的仓库主题入口；不能读完 `framework/` 就直接开始查源码。
4. 仓库主题入口负责继续路由。涉及源码时先看 `components/_index.md` 的职责地图，只属于某个模型时看 `models/_index.md`；确认一个主要 owner 后读取对应 `_index.md` 和其中已有的 `rules.md`，并停止横向展开。只有 live 调用链证明错误跨越另一个模块边界时才读取第二个模块，不能为了保险遍历所有相关目录。找不到 owner 时以 live 源码继续调查，复盘确认稳定边界后再补路由，不要为一次问题临时造模块。
5. 当前机器地址、路径、账号、cache、venv 和临时状态只从 ignored `local/` 获取，并用 live 命令重新验证。
6. 不要递归加载整棵知识树；历史错题不是默认入口，只在规则明确提示、出现高度相似错误或用户明确调查历史时搜索。

## 1. 知识地图：先通用，再仓库，最后代码或模型

| 正在做什么 | 第一个入口 | 识别仓库后必须检查 |
|---|---|---|
| code review、边界和公开接口 | [framework/review](framework/review/_index.md) | `repos/<仓库>/review/_index.md` |
| 测试选择和 CI | [framework/ci](framework/ci/_index.md) | `repos/<仓库>/ci/_index.md` |
| 写文档、RFC 和用户可见说明 | [framework/docs](framework/docs/_index.md) | `repos/<仓库>/docs/_index.md` |
| Git、commit、rebase 和 PR | [framework/git](framework/git/_index.md) | `repos/<仓库>/git/_index.md` |
| 调试和根因收敛 | [framework/debug](framework/debug/_index.md) | `repos/<仓库>/debug/_index.md` |
| benchmark 和性能证据 | [framework/benchmark](framework/benchmark/_index.md) | `repos/<仓库>/benchmark/_index.md` |
| Windows、WSL、编码和本地工具 | [framework/environment](framework/environment/_index.md) | 通常没有仓库补充 |
| SSH、容器、GPU 和远端长跑 | [framework/remote](framework/remote/_index.md) | `repos/<仓库>/remote/_index.md` |
| 多 agent 分工和交接 | [framework/agents](framework/agents/_index.md) | 通常没有仓库补充 |
| 拆需求、产品闭环和执行计划 | [framework/planning](framework/planning/_index.md) | 仓库入口中对应的业务主题 |

仓库补充目录不一定全部存在，不要预先建立空目录。存在同名仓库主题时必须进入；不存在时以仓库 `rules.md` 的现象路由为准。问题同时影响多个位置时只保留一份规则正文，其他入口链接过去。

## 2. 通用 P0 硬停

- **先定目标和边界**：确认真实仓库、分支、用户要求和允许修改的范围。不要把旁边 checkout、历史 worktree 或另一个仓库的规则当成当前目标。
- **Live facts > knowledge**：当前代码、远端状态、PR head、CI、进程、GPU、路径、环境变量和账号身份以本轮 live 证据为准；指南和错题只作线索。
- **No fake evidence**：没有 source、diff、日志或实测证据不下结论。编译通过、shape 正确、stub smoke 和进程已经退出不能替代真实行为验证。
- **No silent fallback**：不要用隐式默认值或静默降级掩盖错误路径。必要 fallback 必须有明确条件、可见信号和验证。
- **No broad kill/delete**：删除、移动或清理前确认绝对路径和归属；远端只清本轮能够证明归属的进程和文件。
- **保护他人状态**：共享机器、旁边仓库、用户已有改动和未跟踪文件默认不属于本轮；未经授权不修改、不清理、不覆盖。
- **公开前做隐私检查**：公开文档、commit、PR、issue 和日志不得包含凭据、私人地址、内网机器信息或用户绝对路径。
- **用户纠正后刷新证据**：用户指出目标或事实错误时，停止维护旧结论，重新确认范围和 live 状态。
- **说人话**：先报告结果、影响和需要决定的事情；内部术语只作为证据。

## 3. 场景触发器

| 用户正在做什么 | 必读入口 | 最低要求 |
|---|---|---|
| 写代码或修改公开接口 | [code taste](framework/review/guides/code-taste.md) | 先理解现有 owner、调用链、测试和用户可见行为 |
| code review 或 reviewer follow-up | [reviewer lens](framework/review/guides/reviewer-lens-audit.md) | 围绕当前 diff 查重复、边界、异常路径和公开影响 |
| UI、CLI、文档或其他用户可见改动 | [用户可见验收](framework/docs/guides/user-visible-acceptance.md) | 绿测之外还要跑普通用户真实路径 |
| benchmark 或性能结论 | [benchmark contract](framework/benchmark/guides/benchmark-contract.md) | 先固定版本、工作负载、指标和证据来源 |
| SSH、容器、远端服务或长跑 | [远端入口](framework/remote/_index.md) | 先验证目标、环境、超时、状态文件和清理边界 |
| 多 agent 或并行工作 | [agent loop](framework/agents/guides/agent-loop-workflow.md) | 只拆能独立验证的任务，主 agent 复核结论 |
| 产品规划或 roadmap | [产品闭环](framework/planning/guides/product-loop-planning.md) | 先写用户可感知的完整闭环，再拆技术任务 |
| 复盘、沉淀经验或总结教训 | [复盘到规则](framework/debug/guides/retrospective-to-rules.md) | 默认更新最近 owner 的规则；只有复杂证据值得长期保留时才新增错题 |

仓库入口链接的 `rules.md` 可以增加更严格的门禁，但不能放宽这里的通用 P0。

## 4. 知识写到哪里

- 能反复避免问题、改变下一次行为的结论 → 最近 owner 的 `rules.md`。跨仓库规则放 `framework/<主题>/`，仓库规则放 `repos/<仓库>/`，模块或模型规则继续下沉到对应目录。
- 稳定的数据流、职责和边界 → 最近 owner 的 `architecture.md`。
- 需要展开说明但不是硬门禁的方法 → 对应主题的 `guides/`。
- `incidents/` 只保存规则无法承载的复杂复现、证据链或历史背景；它可有可无，不能成为正常开工必须猜路径才能找到的知识入口。
- 当前机器事实 → ignored `local/`。

用户要求“复盘”时，必须回答为什么发生、为什么原有规则或测试没有发现、怎样提前阻止，并把可执行结论写进最近 owner 的 `rules.md`。只有事故过程本身仍有独立查询价值时，才同时保留一篇 incident 并从规则链接过去。

长期知识禁止写入系统、全局或个人 memory 位置。新增、移动、拆分或删除 Markdown 前读 [CONTRIBUTING.md](CONTRIBUTING.md)，同步最近的 `_index.md`，然后运行：

```powershell
python tools/check_knowledge_tree.py
```

## 5. Git 和公开修改

- 先读 [通用 Git 入口](framework/git/_index.md)，再读当前仓库自己的 Git/PR 规则。
- 提交前确认 diff、分支、remote、作者身份、签名要求和目标 PR；这些不能从其他仓库继承。
- 用户只要求分析、解释或 review 时，不自动 commit、push、改 PR 或修改外部状态。
- 用户明确要求发布时，只发布已经确认属于本轮的文件；未跟踪输出和其他人的改动默认排除。

## 6. 总入口

- 通用经验：[framework/_index.md](framework/_index.md)
- 仓库经验：[repos/_index.md](repos/_index.md)
- 贡献与目录维护：[CONTRIBUTING.md](CONTRIBUTING.md)
- 当前机器信息：ignored `local/`
