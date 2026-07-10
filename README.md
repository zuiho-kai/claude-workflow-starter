# Workflow Starter

这是一套可以直接用 Markdown 手工维护的项目知识框架。它把跨仓库通用方法、仓库专有经验、代码模块、模型和错题放在一棵目录树中，避免每次任务把无关内容全部加载。

## 开始使用

```bash
git clone https://github.com/zuiho-kai/claude-workflow-starter.git
cd claude-workflow-starter
```

如果还需要项目代码，可以把目标仓库克隆到旁边或按自己的 worktree 规则管理。知识仓库用 `repos/<仓库>/` 表示经验归属，不要求把项目代码塞进这个目录。

## 从哪里查

- [通用经验](framework/_index.md)：review、CI、docs、Git、debug、benchmark、环境、远端、agent 和规划。
- [仓库经验](repos/_index.md)：当前登记了 vLLM-Omni 和 Jianghan。
- [HunyuanImage3](repos/vllm-omni/models/hunyuan-image3/_index.md)：模型架构、HF 对齐、历史分析和错题。
- [目录维护规则](docs/framework_layout.md)：内容放哪里、错题怎么写、什么时候拆分、怎样更新索引。

不知道归属时，可以先全文搜索：

```powershell
rg "SSH timeout|shape mismatch" framework repos -g "*.md"
```

## 目录怎样理解

```text
framework/<主题>/                         # 换仓库仍然成立
repos/<仓库>/<主题>/                      # 某仓库专有流程
repos/<仓库>/components/<代码模块>/       # 前端、后端、diffusion 等共享代码
repos/<仓库>/models/<模型>/               # 模型专有实现和配置
<最近目录>/incidents/                     # 具体错题
local/                                    # 当前机器信息，Git 忽略
```

每个正式目录都有 `_index.md`，说明什么时候查、什么不放这里，以及每个页面的入口。普通维护者不需要编辑 YAML 或修改检查脚本。

## 新增普通经验

1. 判断内容属于通用主题、仓库、代码模块还是模型。
2. 在最接近的目录中新建 Markdown。
3. 在同目录 `_index.md` 增加一行“遇到什么 → 查看哪里”。
4. 运行：

   ```powershell
   python tools/check_knowledge_tree.py
   ```

也可以从 `templates/` 复制最接近的例子；不用模板也能完整手工添加。

## 新增错题

错题按根因放在最近的 `incidents/`：

- 通用 SSH、WSL、PowerShell 或 Git 错误 → `framework/<主题>/incidents/`
- 仓库 CI、benchmark、review 或 remote 错误 → `repos/<仓库>/<主题>/incidents/`
- 多模型共享代码错误 → `repos/<仓库>/components/<模块>/incidents/`
- 模型专有错误 → `repos/<仓库>/models/<模型>/incidents/`

文件名使用 `YYYY-MM-DD-short-name.md`，正文从 [错题模板](templates/incident.md) 开始。一件事故只保留一篇完整正文，其他目录用链接指过去。

## 内容多了怎样拆

- 单文件达到 300 个非空行或 16 KiB：检查是否已经混入多个主题。
- 单文件达到 500 个非空行或 32 KiB：必须拆分，或在 `_index.md` 写明暂不拆的原因和复核日期。
- 一个目录直接放到第 8 个普通页面：按 `guides/`、`incidents/` 或明确业务主题分类。
- 一个分类目录超过 20 篇当前有效页面：继续按稳定问题主题分类。

工具只提醒、生成模板和修复确定无歧义的链接，不会静默决定语义归属或后台移动文件。

## 当前机器信息

真实服务器地址、账号、token、私钥、cache 和 venv 路径只放 Git 忽略的 `local/`。可以从模板开始：

```powershell
Copy-Item templates/remote-server.md local/remote.md
```

正式知识页面不得包含私人 host、凭据或用户绝对路径。去除敏感信息后仍有复用价值的教训，再写入 `framework/` 或 `repos/`。

## 自动检查

```powershell
python tools/check_knowledge_tree.py
```

它会检查：

- 每个目录是否有 `_index.md`；
- 页面和子目录是否登记到最近索引；
- 相对链接是否存在；
- 错题的文件名、编号、归属、状态和入口是否完整；
- 文件和目录是否超过拆分限制；
- `local/` 是否意外进入 Git。

脚本不会判断两篇文章是否语义重复，也不会替人决定问题属于哪个代码模块或模型。

## 主要入口

| 内容 | 路径 |
|---|---|
| 开工硬规则 | `CLAUDE.md` |
| 通用经验 | `framework/` |
| 仓库、代码模块、模型和错题 | `repos/` |
| 可复制模板 | `templates/` |
| 当前机器信息 | `local/`（Git ignored） |
| 目录设计 | `docs/framework_layout.md` |
| 索引检查 | `tools/check_knowledge_tree.py` |

框架目标只有一个：让人和 agent 都能沿清晰入口找到需要的最少内容，并且让新经验在下一次任务中真正可查。
