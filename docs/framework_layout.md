# 知识框架目录设计

状态：**已实施，2026-07-10。本文同时作为目录维护规范。**

## 1. 设计目标

这套目录首先服务人类，其次才服务自动化。维护者应该只看目录名和 `_index.md` 就知道：

- 一条经验适用于所有仓库，还是只适用于某个仓库；
- 应该去 review、CI、docs、benchmark、remote 等哪个主题查；
- 问题属于整个仓库、某个代码模块，还是某个模型；
- 新增、移动或拆分文件时，需要同步修改哪些入口。

只保留一套正式知识目录，不建立 `_private/` 或第二套私人索引。

机器地址、token、私钥、账号、内网地址和用户绝对路径不属于知识，统一放在 Git 忽略的 `local/`。去除这些敏感信息后仍有复用价值的经验，直接写入正式目录。

## 2. 最终目录

```text
CLAUDE.md                              # 很短的总入口和必须遵守的规则
README.md

framework/                            # 换一个仓库仍然成立的通用经验
  _index.md
  review/
    _index.md
    guides/                           # 有内容才创建
      _index.md
    incidents/                        # 有错题才创建
      _index.md
  ci/
    _index.md
  docs/
    _index.md
  git/
    _index.md
  debug/
    _index.md
  benchmark/
    _index.md
  environment/
    _index.md
  remote/
    _index.md
  agents/
    _index.md
  planning/
    _index.md

repos/                                # 每个仓库自己的经验
  _index.md
  vllm-omni/
    _index.md
    rules.md                          # 仓库通用硬规则，有需要才创建
    architecture.md                   # 尚未拆代码模块时的系统总览，可选
    review/
      _index.md
    ci/
      _index.md
      incidents/
        _index.md
    docs/
      _index.md
      rfcs/
        _index.md
    git/
      _index.md
    benchmark/
      _index.md
    remote/
      _index.md
    dev/
      _index.md
    components/                       # 前端、后端、diffusion 等代码模块
      _index.md
      diffusion/
        _index.md
        architecture.md
        incidents/                    # 有错题才创建
          _index.md
      model-executor/
        _index.md
        architecture.md
    models/                           # 各模型的专有经验
      _index.md
      hunyuan-image3/
        _index.md
        architecture.md
        incidents/                    # 有错题才创建
          _index.md

  jianghan-roleplay-data-pipeline/
    _index.md
    rules.md
    pipeline/
      _index.md

templates/                            # 可直接复制的目录和页面模板
  topic/                               # review、CI、docs 等主题目录模板
  repo/                                # 仓库目录模板
  component/                           # 前端、后端、diffusion 等代码模块模板
  model/                               # 模型目录模板
  incident.md                          # 错题页面模板

local/                                # Git 忽略，只放当前机器的信息
tools/
skills/
```

不预先提交空目录。第一次有真实内容时，再同时创建目录和 `_index.md`。

## 3. 怎样判断放在哪里

新增内容时按下面顺序判断：

1. 换到完全无关的仓库后仍然正确吗？是就放 `framework/<主题>/`。
2. 依赖某个仓库的代码、规则、命令或流程吗？放 `repos/<仓库>/<主题>/`。
3. 根因属于一个会被多处使用的代码模块吗？放 `repos/<仓库>/components/<模块>/`。
4. 根因只属于某个模型的实现、配置、checkpoint 或专有流程吗？放 `repos/<仓库>/models/<模型>/`。
5. 只是当前机器的地址、路径、缓存、环境或账号吗？放 `local/`，不要写进知识页面。

`review`、`ci`、`docs`、`benchmark`、`remote`、`dev` 表示“正在做哪类工作”。

`components/frontend`、`components/backend`、`components/diffusion` 表示“事实属于哪块代码”。

`models/hunyuan-image3` 表示“事实只属于哪个模型”。

这三类目录平级存在，不互相套娃：

```text
# 不要这样
repos/acme/dev/frontend/incidents/
repos/vllm-omni/ci/models/hunyuan-image3/

# 应该这样
repos/acme/dev/
repos/acme/components/frontend/
repos/vllm-omni/ci/
repos/vllm-omni/models/hunyuan-image3/
```

如果一个问题同时影响多个位置，只保留一篇正文，其他位置用链接指过去。

## 4. `_index.md` 应该怎么写

每个正式知识目录都必须有 `_index.md`。它是给人看的目录说明，不要求维护者学习 YAML 或额外配置格式。

统一模板：

```markdown
# Diffusion

## 什么时候查这里

- 调查 diffusion runner、scheduler、DiT 或多个 diffusion 模型共用的实现。

## 不放什么

- HunyuanImage3 独有实现放到 `models/hunyuan-image3/`。
- 通用 benchmark 方法放到 `framework/benchmark/`。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 理解当前数据流 | [architecture](architecture.md) | 当前公开架构 |
| 调查历史故障 | [incidents](incidents/_index.md) | 具体错题 |
```

每个 `_index.md` 必须写清：

1. 什么时候查这里；
2. 哪些内容不属于这里；
3. 当前目录和直接子目录中每个页面的入口；
4. 每个入口适用于什么问题。

页面的搜索词直接写进“遇到什么”这一列，不再要求普通页面重复填写触发词。

### 仓库入口

`repos/<仓库>/_index.md` 额外写明：

```markdown
# vLLM-Omni

- 上游仓库：`vllm-project/vllm-omni`
- 适用范围：vLLM-Omni 的开发、测试、文档、模型和远端验证
```

同时列出该仓库现有的主题、代码模块和模型入口。

### 代码模块入口

`components/<模块>/_index.md` 额外列出：

- 对应源码路径；
- 主要职责；
- 相关测试入口；
- 会影响哪些模型或上层功能。

### 模型入口

`models/<模型>/_index.md` 额外列出：

- 模型正式名称和常见别名；
- 对应源码路径；
- 依赖哪些代码模块；
- checkpoint、尺寸或量化版本之间的差异。

## 5. 每一层默认放什么

### 通用主题：`framework/<主题>/`

只放换一个仓库仍然成立的方法。例如：

- `framework/review/`：怎样判断代码归属、重复实现、边界情况和公开接口影响。
- `framework/ci/`：怎样选择针对性测试、完整测试和发布前验证。
- `framework/docs/`：怎样确认文档的真实来源、更新链接和避免过期副本。
- `framework/benchmark/`：怎样固定测试口径、预热方式、指标和结果来源。
- `framework/remote/`：怎样安全使用 SSH、容器、超时、清理和长跑任务。

这里不能出现某个仓库专有命令、模型专有结论或私人机器地址。

### 仓库主题：`repos/<仓库>/<主题>/`

只写该仓库相对通用方法的差异。例如：

- vLLM-Omni 使用哪些 CI 层级；
- 它的 benchmark 配置从哪里进入请求；
- 它的 RFC、文档和 PR 规则；
- 它的远端验证需要哪些仓库专有步骤。

不要复制 `framework/` 的整篇正文，只写仓库特有内容并链接通用页面。

### 代码模块：`repos/<仓库>/components/<模块>/`

默认只有：

```text
_index.md
architecture.md
```

前端、后端、API、diffusion、serving、scheduler 等可以成为代码模块，但至少应满足下面一项：

- 有独立源码目录；
- 有独立维护人或测试命令；
- 有独立运行流程或输入输出边界；
- 同一套知识会影响多个模型或多个工作主题。

### 模型：`repos/<仓库>/models/<模型>/`

默认只有：

```text
_index.md
architecture.md
```

不要为每个 checkpoint、尺寸或量化版本建立文件夹。它们先作为同一个模型入口中的别名和差异说明。

只有源码、配置含义、checkpoint 语义或完整运行流程真正不同，才建立新的模型目录。

### `guides/`、`incidents/`、`rfcs/` 等分类目录

这些目录只用于把同类页面放在一起。创建时必须同时创建 `_index.md`，并在上一层 `_index.md` 增加入口。

分类目录的 `_index.md` 必须列出里面的每篇当前有效页面。已经过期但仍有历史价值的页面单独分组，不与当前规则混在一起。

### `local/`

只放当前机器的信息，例如：

- SSH 地址和端口；
- cache、venv 和工作目录；
- 账号、token、私钥位置；
- 本机临时状态。

`local/` 不保存通用教训或错题正文，不被任何正式 `_index.md` 链接，并且不能有被 Git 跟踪的文件。

## 6. 错题本怎么放

### 先判断错误属于哪里

| 错误类型 | 放置位置 |
|---|---|
| 通用 SSH、WSL、PowerShell、文档或 Git 错误 | `framework/<对应主题>/incidents/` |
| 某仓库的 CI、benchmark、review、remote 流程错误 | `repos/<仓库>/<对应主题>/incidents/` |
| 多个模型共用的 diffusion、serving、frontend、backend 错误 | `repos/<仓库>/components/<模块>/incidents/` |
| 某模型专有实现、配置或 checkpoint 错误 | `repos/<仓库>/models/<模型>/incidents/` |

根因还没查清时，先放最接近的仓库主题，在标题标明“待归类”。查清后移动到最终位置，并在同一次修改中更新所有链接。

一件事故只保留一篇完整正文。其他目录只能链接，不能复制一份相似内容。

### 文件名

```text
YYYY-MM-DD-short-name.md
```

例如：

```text
2026-07-10-ssh-timeout-after-container-restart.md
```

### 页面开头

不用 YAML，直接写人能读懂的字段：

```markdown
# 容器重启后 SSH 连接超时

- 编号：`inc-2026-07-10-ssh-timeout`
- 归属：`framework/remote`
- 状态：处理中
- 搜索词：SSH、timeout、container restart
- 影响范围：远端验证
```

状态只使用以下五种说法：

- `待归类`：还不知道最终应该放哪里。
- `处理中`：原因或修复尚未验证。
- `已验证`：原因、修复和验证证据完整。
- `已提炼`：稳定规则已经写进 guide、rules 或 architecture。
- `仅历史`：对当前代码不再适用，但仍值得保留。

状态变化不要求移动文件，避免链接反复变化。

### 正文模板

```markdown
# 一句话故障标题

- 编号：`inc-YYYY-MM-DD-short-name`
- 归属：`repos/example/ci`
- 状态：处理中
- 搜索词：……
- 影响范围：……

## 当时在做什么

版本、任务和必要前提。不要写私人地址、token 和用户绝对路径。

## 看到了什么

用户能观察到的现象和最小错误信息。

## 会造成什么影响

失败、错误判断或潜在风险。

## 真正原因

已经验证的原因。没有验证时明确写“当前猜测”。

## 怎样修复

实际有效的修改或正确操作。

## 怎样证明修好了

测试命令、实际运行结果或其他证据。

## 下次怎样避免

可以重复执行的检查步骤或规则。

## 相关资料

代码、issue、PR、日志摘要或相关知识页面。
```

不要把聊天流水账、完整长日志、未经验证的猜测或只有本机路径的记录当成长期错题。长日志只保留关键错误信息和原始产物位置。

新增错题时，必须在同一次修改中更新所属 `incidents/_index.md`。

如果已经从错题提炼出稳定规则，在错题末尾增加“已提炼到”链接；规则页面不需要复制整篇事故经过。

## 7. 内容多了以后怎样拆

### 单个文件太长

检查脚本同时查看非空行数和文件大小：

| 大小 | 怎么处理 |
|---|---|
| 达到 300 个非空行或 16 KiB | 提醒检查是否已经包含两个以上独立主题 |
| 达到 500 个非空行或 32 KiB | 必须按主题拆分；特殊情况要在同目录 `_index.md` 写明不拆的原因和复核日期 |

不能机械地每 300 行切一刀。应该按独立用户流程、独立代码模块、独立输入输出或独立验证方式拆分。

### 一个目录文件太多

- 一个知识目录可以先直接放最多 7 个普通内容页；`_index.md`、`rules.md`、`architecture.md` 不计入。
- 出现第 8 个普通内容页，或者已经有 3 篇明显属于同一主题时，检查脚本提醒建立 `guides/`、`incidents/` 或有明确含义的分类目录。
- 一个分类目录超过 20 篇当前有效页面时，必须继续按稳定主题分类。
- 分类最多再向下增加一层，避免重新形成很深的目录。
- 错题优先按问题主题分类，例如 `incidents/serving/`、`incidents/scheduler/`，不要一开始就按年份分类。
- 只有错题超过 50 篇，才允许增加年度历史入口；文件真正属于哪里仍由问题主题决定。

这些数字用于阻止目录无限堆积，不表示达到数字后由工具自动乱移动文件。

### 从一个 `dev` 发展成前端和后端

项目早期可以只有：

```text
repos/acme/
  _index.md
  architecture.md
  dev/
    _index.md
```

`dev/_index.md` 可以直接写少量全仓开发规则，不需要提前创建 frontend/backend。

当代码已经明显形成前端和后端，并且下面四项中至少有两项各自独立时，再拆分：

- 源码目录；
- 测试命令；
- 部署方式；
- 运行流程或输入输出。

拆分后：

```text
repos/acme/
  dev/
    _index.md                       # 仍放前后端共用的开发流程
  components/
    _index.md
    frontend/
      _index.md
      architecture.md
    backend/
      _index.md
      architecture.md
```

不要拆成 `dev/frontend/backend`。`dev` 是工作主题，frontend/backend 是代码模块。

仓库根部的 `architecture.md` 拆分后继续保留系统总览和前后端数据流；具体实现分别写到 frontend/backend。

### 模型或代码模块继续变大

- checkpoint 和模型尺寸增加：先补充别名和差异，不新建目录。
- 模型出现完全独立的源码、配置含义或运行流程：新建并列的模型目录。
- 一个代码模块出现至少两个独立源码区域，而且各自有独立架构和测试方式：拆成并列的代码模块。
- `architecture.md` 太长但仍然只有一块代码：拆成同目录下的专题页面，不要虚构新的代码模块。

### 工具可以自动做什么

工具可以：

- 达到上述数字时给出提醒或阻止继续提交；
- 生成新目录和 `_index.md` 模板；
- 更新确定无歧义的相对链接；
- 列出准备移动的文件，让人确认。

工具不能：

- 静默决定一个页面属于前端、后端、通用主题或模型；
- 在后台自行移动文件；
- 只因为行数到了就把一篇文章机械切碎。

## 8. 新增、移动和拆分时必须同步什么

任何 Markdown 新增、移动、重命名、拆分或删除时，都必须在同一次修改中：

1. 更新当前目录的 `_index.md`。
2. 如果创建或删除了子目录，更新上一层 `_index.md`。
3. 修复所有指向旧路径和新路径的相对链接。
4. 移动错题时保持“编号”不变，只修改“归属”和路径。
5. 删除已经被新页面替代的重复正文。
6. 运行检查脚本，确认没有漏进索引的页面和断开的链接。

拆分完成必须满足：

- 旧文件不再继续接收新内容；
- 每个新页面都能从最近的 `_index.md` 找到；
- 上一层入口能找到新建的子目录；
- 全仓没有仍指向旧路径的有效链接；
- `CLAUDE.md` 不因为底层文件移动而增加大量细节。

## 9. 人类怎样手工添加内容

### 新增一个仓库、主题、代码模块或模型

1. 可以复制 `templates/` 中最接近的示例，也可以手工创建目录。
2. 创建 `_index.md`，写清“什么时候查”“不放什么”和“目录内容”。
3. 在上一层 `_index.md` 增加入口。
4. 添加真实内容，不提交空目录。
5. 运行检查脚本。

### 新增一个普通页面

1. 在最接近的目录中新建 Markdown。
2. 在当前目录 `_index.md` 增加一行链接和适用场景。
3. 如果达到文件或目录拆分数字，同一次修改完成整理。
4. 运行检查脚本。

目录名统一使用小写英文、数字和短横线，例如 `remote-debug`。同一层不能重名。`_index`、`local`、`components`、`models`、`incidents`、`guides`、`templates` 是框架已有名字，不用于自定义主题名。

添加新目录不需要修改检查脚本中的固定名单；只要上一层 `_index.md` 能找到它即可。

## 10. 检查脚本应该检查什么

检查脚本负责容易明确判断的事情：

- 每个正式知识目录都有 `_index.md`；
- 每个当前有效页面都能从最近的 `_index.md` 找到；
- 每个页面只在一个最近入口中登记正文位置，其他位置只能链接；
- 所有相对链接指向存在的文件；
- 目录层级和文件数量没有超过约束；
- 错题文件名、编号、归属、状态和索引登记完整；
- `local/` 没有被 Git 跟踪的文件；
- 正式 Markdown 没有明显的 token、私钥、私人地址、账号或用户绝对路径。

检查脚本不假装理解文章语义。下面这些事情必须由人或人工评审判断：

- 两篇文章是不是在讲同一件事；
- 错题最终属于哪个代码模块或模型；
- 一个大文件应该按什么主题拆；
- 仓库专有页面是否复制了太多通用正文。

## 11. 查询时怎样避免又慢又乱

每次查询只沿需要的入口向下读：

1. 先确认当前仓库。
2. 根据任务选择一个通用主题。
3. 有仓库专有页面时再读取同名仓库主题。
4. 只有问题明确属于某块代码或某个模型时，才读取对应目录。
5. 历史错题只在出现相似错误或用户明确调查历史时搜索。

不要在每次任务开始时递归读取所有 Markdown。

不知道错误属于哪里时，可以直接全文搜索：

```powershell
rg "SSH timeout|shape mismatch" framework repos -g "*.md"
```

因为所有正式经验都在同一棵目录树中，所以不需要另一份私人搜索入口。

## 12. 当前写入规则

- 新的通用经验只写 `framework/`。
- 新的仓库、代码模块、模型和具体错题只写 `repos/`。
- 当前机器事实只写 ignored `local/`。
- 新增或移动页面必须同步最近的 `_index.md`，并运行 `python tools/check_knowledge_tree.py`。
- 不再建立兼容副本或第二套写入路径；历史位置只通过 Git history 查询。

## 13. 完成标准

- 不熟悉框架的人只看根目录和 `_index.md` 就能找到入口。
- 通用 review 不会加载任何仓库专有内容。
- vLLM-Omni CI 只读取通用 CI 和 `repos/vllm-omni/ci/`。
- HunyuanImage3 任务能找到 `repos/vllm-omni/models/hunyuan-image3/`。
- diffusion 共享错误进入 `components/diffusion/incidents/`，模型专有错误进入对应模型目录。
- 前端、后端等代码模块与 dev、review、CI 等工作主题平级，不互相套娃。
- 每篇错题只有一份完整正文，并有稳定编号、验证证据和索引入口。
- 超过大小限制的文件和目录已经整理，或明确写明暂不拆分的原因和日期。
- 每个当前有效页面都能从最近的 `_index.md` 找到，所有相对链接有效。
- 第三方只需创建目录、写 Markdown 和更新上一层 `_index.md`，不需要理解额外配置系统。
- 全局全文搜索可以找到 `framework/` 和 `repos/` 下的所有正式经验。
- `local/` 没有被 Git 跟踪的文件，`CLAUDE.md` 仍然只是短入口。

本规范已经实施。后续结构调整必须先修改本文，再在同一次变更中更新模板、检查脚本和受影响索引。
