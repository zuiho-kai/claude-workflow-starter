# Workflow Starter 开工入口

本文件只负责三件事：告诉 agent 先读哪里、哪些通用风险必须硬停、长期知识应该写到哪里。仓库、代码模块、模型和机器专属规则不写在这里。

## 0. 开工顺序

1. 确认用户正在操作哪个真实仓库；不要用当前 shell 路径或历史对话猜。
2. 从下面的知识地图选择一个匹配的 `framework/<主题>/_index.md`。
3. 从 [仓库列表](repos/_index.md) 找当前仓库；存在时读取 `repos/<仓库>/_index.md` 和它链接的 `rules.md`。
4. 只有问题明确属于共享源码模块时才进入 `components/<模块>/`，只属于某个模型时才进入 `models/<模型>/`。
5. 当前机器地址、路径、账号、cache、venv 和临时状态只从 ignored `local/` 获取，并用 live 命令重新验证。
6. 不要递归加载整棵知识树；历史错题只在出现相似错误或用户明确调查历史时搜索。

## 1. 知识地图：先通用，再仓库，最后代码或模型

| 正在做什么 | 第一个入口 | 仓库有特殊规则时再看 |
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

仓库补充目录不一定全部存在，不要预先建立空目录。问题同时影响多个位置时只保留一篇正文，其他入口链接过去。

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

仓库入口链接的 `rules.md` 可以增加更严格的门禁，但不能放宽这里的通用 P0。

## 4. 知识写到哪里

- 换到无关仓库仍然成立的方法 → `framework/<主题>/`。
- 依赖某仓库代码、命令、CI、PR 或流程的经验 → `repos/<仓库>/<主题>/`。
- 多处复用的源码模块事实 → `repos/<仓库>/components/<模块>/`。
- 模型专有实现、配置和 checkpoint 语义 → `repos/<仓库>/models/<模型>/`。
- 具体错误 → 最近归属目录的 `incidents/`。
- 当前机器事实 → ignored `local/`。

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
