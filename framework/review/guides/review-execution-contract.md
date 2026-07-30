# 独立审查执行合同

**何时使用：** 开发完成后的独立 review、完整 diff review、准备交给项目 owner 前的最后审查。这里是可直接执行的短入口；风险解释和专项 lens 只在本页要求时继续读取。

## 完成条件

审查分三轮，顺序不能交换：

1. **覆盖轮：** 冻结基线和完整 diff。owner 定义审查触发组时，选择 `core` 加当前 diff 命中的组并完整枚举组内稳定 ID；没有触发组时才枚举该 owner 全部稳定 ID。随后填写当前可达公开入口和 changed-value producer→consumer 表。
2. **减法轮：** 读取编码前生产预算，统计实际 production additions、files 和新增 abstraction。先按共同输入、owner artifact 和连续 transformation 把新增 abstraction 归簇，为每簇写出不依赖当前实现的最小 owner 设计；再对每个新增 helper、class、normalizer、validator、allowlist、compiler、中间对象或独立路由流程给出 `INVARIANT:`、`REUSE:` 或 `NET_DELETE:` 生存证明。缺少编码前预算、当前 abstraction 总数大于最小 owner 设计、或任一项给不出证明时必须形成 blocking finding；不能用测试数量、历史 comment 数量、多 caller 或“以后扩展”证明其必要。
3. **开放轮：** 再查 duplication、layering、edge cases、surface area 和命中的专项风险。

找到很多新问题不能代替覆盖轮或减法轮。不能为了省事漏掉命中组，也不能为了“更全面”把未触发组全部展开成噪声。缺少所选规则行、可达入口、changed-value consumer、编码前预算或新增 abstraction census 时，结论只能是 `partial review`；不能说 `clean`、`ready` 或 `fully reviewed`。

同一用户语义如果有多个输入来源、dispatcher、stage 类型或兼容入口，覆盖轮还必须先写完**来源 × consumer scope 决策矩阵**，再读具体实现。每个 source/scope 单元格只能标成：路由到哪个 consumer、与哪些来源重复时拒绝、明确不适用，或非用户 default；不能留给字典合并顺序和分支先后隐式决定。至少验证每个合法单来源、每组同 scope 重复、一个跨 scope 共存 control，以及每条 production dispatcher 的等价结果。矩阵缺失时，即使当前测试和开放轮没有 finding，也只能报 `partial review`。

PR 声称“严格校验”“拒绝未知字段”“统一 normalization”或其他全入口行为时，公开入口不能只按 changed hunk 或当前 production caller 枚举。必须搜索同一合同的所有可调用 constructor、factory、classmethod、兼容 helper 和旧入口，包括本次未修改、已退出当前主调用链但仍可被仓库测试或外部调用者直接使用的入口；对每个入口运行同一个最小负向样例并记录结果。任一入口仍静默接受、过滤或覆盖该样例时，整体合同未闭环；如果宽松行为确属兼容要求，必须有明确文档、专门回归测试和不把它算作严格入口的 scope 声明。只证明两条 production 路径严格，不能据此宣称整个配置或 API surface 已严格化。

## Reviewer 只读输入

- 用户需求和允许修改的范围；
- 固定的 target/base SHA；
- 当前完整 diff，以及属于任务的未跟踪文件；
- live 调用链证明的 owner `rules.md`；
- 每个 owner 的规则组选择及触发理由；有触发组时必须包含 `core`，选择和覆盖完整性由审查负责人复核；
- 编码前已存在的 mini spec 或合同矩阵；不存在时记 `MISSING_EVIDENCE`，不能事后代写；
- 必要的仓库源码、测试和官方实现。

不要给 reviewer 作者自评、怀疑根因、历史 reviewer 答案或 incidents。规则直接指向 owner 后停止读其他文档，但**停止读文档不等于停止追源码**：必须继续覆盖所有能到达同一 consumer 的公开入口和跨 owner 调用边界。

## Owner 怎样声明审查组

小 owner 可以不分组，继续全量审计。规则较多时，在 `rules.md` 放一张人能直接编辑的表；一旦使用分组，必须有 `core`，每个稳定 ID 至少属于一个组，组名只用小写字母、数字和连字符。开发路由规则可以放 `author-routing`，不要塞进每次代码 review 的 `core`。

```markdown
| 审查组 | 什么时候触发 | 规则 ID |
|---|---|---|
| `core` | 每次代码审查 | `ABC-1a`, `ABC-1b` |
| `public-topology` | CLI、API、资源获取或 topology 改动 | `ABC-2a`, `ABC-2b` |
```

第三方新增 owner 时只需手工增加同样的表和稳定 ID；稳定 ID 可以使用 `ABC-1a` 或 `VOMNI-CFG-1a` 这类多段大写前缀。规则组和 ID 是给 reviewer 定位语义用的，不是 Markdown 解析协议。

## 审查报告

报告服务真实 maintainer，不服务格式检查器。可以使用段落、列表或表格，只要人能直接核对以下内容：

- 固定的 base/head、owner、所选规则组和属于任务的未跟踪文件；
- 每个命中稳定 ID 的结论、代码证据和测试或运行证据；
- 当前可达公开入口、changed value 的 producer→consumer 路径，以及多来源时的冲突或路由决策；
- 编码前预算、实际 production delta、新增 abstraction census、最小 owner 设计和逐项生存证明；
- 每个 finding 的严重度、可达失败路径、原有合同、反证和最小修复；
- 未验证项的具体阻塞，以及最终是 clean、partial review 还是 implementation draft。

没有固定章节名、表头、反引号、英文 token、统计句式或机器尾签要求。规则页没有稳定 ID 时，reviewer 直接引用相关原文并说明覆盖边界；不要把自然语言段落机械编号成 legacy rule。审查负责人必须重新读取报告和规则页，人工确认没有漏掉所选 ID、入口、consumer、abstraction 或 finding；不能用脚本结构通过代替语义复核。

格式问题永远不是代码 finding。只有证据证明当前 diff 引入了可达失败、违反既有合同或缺少完成所需行为验证时，才能形成 blocking finding。

## 何时继续读取详细指南

- 需要完整可粘贴 prompt 或专项 owner 角色：[reviewer lens prompt](reviewer-lens-prompt.md)
- 涉及 async、资源生命周期、性能证据或 rebase：[reviewer lens gates](reviewer-lens-gates.md)
- 需要理解四类开放审查方法：[reviewer lens audit](reviewer-lens-audit.md)
- public API、跨阶段字段或协议矩阵：[reviewer lens contracts](reviewer-lens-contracts.md)
