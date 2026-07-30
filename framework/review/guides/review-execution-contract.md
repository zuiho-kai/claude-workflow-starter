# 独立审查执行合同

**何时使用：** 开发完成后的独立 review、完整 diff review、准备交给项目 owner 前的最后审查。这里是可直接执行的短入口；风险解释和专项 lens 只在本页要求时继续读取。

## 完成条件

审查分三轮，顺序不能交换：

1. **覆盖轮：** 冻结基线和完整 diff。owner 定义审查触发组时，选择 `core` 加当前 diff 命中的组并完整枚举组内稳定 ID；没有触发组时才枚举该 owner 全部稳定 ID。随后填写当前可达公开入口和 changed-value producer→consumer 表。
2. **减法轮：** 读取编码前生产预算，统计实际 production additions、files 和新增 abstraction。先按共同输入、owner artifact 和连续 transformation 把新增 abstraction 归簇，为每簇写出不依赖当前实现的最小 owner 设计；再对每个新增 helper、class、normalizer、validator、allowlist、compiler、中间对象或独立路由流程给出 `INVARIANT:`、`REUSE:` 或 `NET_DELETE:` 生存证明。缺少编码前预算时记 `MISSING_EVIDENCE`，阻止 `clean/ready` 结论但不能冒充代码 finding；当前 abstraction 总数大于最小 owner 设计、或任一项给不出生存证明时才形成 blocking finding。不能用测试数量、历史 comment 数量、多 caller 或“以后扩展”证明其必要。
3. **开放轮：** 再查 duplication、layering、edge cases、surface area 和命中的专项风险。

找到很多新问题不能代替覆盖轮或减法轮。不能为了省事漏掉命中组，也不能为了“更全面”把未触发组全部展开成噪声。缺少所选规则行、可达入口、changed-value consumer、编码前预算或新增 abstraction census 时，结论只能是 `partial review`；不能说 `clean`、`ready` 或 `fully reviewed`。

任一轮发现 P0/P1/P2 都不能提前结束其余轮次。最终报告必须分别给出 **subtraction verdict** 和 **correctness verdict**：前者列出 scope 删除项与架构减法，或用完整 ledger 证明当前已是最小设计；后者列出行为 finding 或 clean 证据。只给一个综合的“建议/不建议合并”，或用 blocking bug 代替减法结果，审查仍未完成。

### 默认双角色

每次 PR review 都包含两个不可互相替代的角色：

- **Correctness reviewer：** 从公开入口追 producer→consumer，检查行为、错误合同、兼容路径、默认值、最终 consumer 和测试证据。
- **Design/subtraction reviewer：** 先做 project-level scope subtraction，对齐用户目标和当前 RFC/mini spec 切片，删除越界 behavior、文件和测试；再做 module-level architecture subtraction，检查唯一 owner、最小数据流、最小修改、现有 abstraction 复用，以及可删除、合并、内联或迁回既有 owner 的层。

有 multi-agent 能力时，非琐碎 PR 的审查负责人在冻结 base/head 和授权合同后，必须立即调用委派能力并行启动两个独立只读 reviewer；不能只在 prompt 里描述两个角色，也不能由同一 agent 悄悄兼任。两个 reviewer 使用相同冻结输入，不能互看 finding：

- correctness reviewer 返回可达入口、producer→consumer、行为 finding、反证和测试边界；
- design/subtraction reviewer 必须同时返回 project-level scope ledger，以及 module-level census、最小设计、逐项 `KEEP / INLINE / MERGE / MOVE / DELETE` 账本和净结果。

审查负责人必须等待两个结果再收口。单文件且没有新增 public behavior、owner、abstraction 或兼容路径的窄 diff 可以由一个 reviewer 顺序执行两个角色，但仍必须分别交付两个 verdict。当前环境确实不能委派时，明确写“multi-agent unavailable”，再由主 agent 顺序执行；不得把未尝试委派说成能力不可用。任一角色缺失都只能报 `partial review`。

### 解释压力反查

减法轮必须用当前最终 head 做一次不依赖提交历史的“人话解释”：只说现在有哪些输入、每个 source × scope 的唯一 owner 规范产物是什么、谁最终消费，不能按 commit、review comment 或修复时间线解释。如果必须靠历史才能说明当前结构，先判定当前设计本身没有自洽。

解释时出现下面任一信号，reviewer 必须回到代码定位对应结构，不能只润色文档或增加注释：

- 两个字段组、helper 或中间对象没有不同 consumer，最终只是立即求并集、转发或拆开后再合并；
- 同一 owner 产物跨层不断换名，尤其把已校验 projection 又叫回 raw request、`extra_body`、kwargs 或 config；
- normalizer、builder 或 materializer 已产出最终值，下游 dispatcher、consumer 或 model 仍要重新读原始输入、补默认值、重做 alias 或再次决定优先级；
- 用户要求或编码前 mini spec/合同声明某职责是 non-goal，但 production diff 又修改了该职责的真实 consumer；
- 无法为每个 source × scope 单元指出一次明确的 `输入 → owner 规范产物 → 最终 consumer`；合法的 representation 或 lifecycle adapter 可以保留，但必须消费同一规范产物，不能重新决定语义。owner-local legacy fallback 若已在矩阵声明优先级且最终只产出一个规范值，不算重复 owner。

每个命中信号必须写出“当前结构 → 不依赖当前实现的最小结构 → 可删除或应迁移的具体项”。只有能证明 representation、lifecycle 或 failure-policy 不同，才允许保留额外层；“兼容复杂”“测试很多”“这样更清晰”不是反证。解释困难本身不是 blocking finding，但它触发的重复 abstraction、错误 owner、误导命名或末端补偿必须进入正式 finding。

### 减法轮交付合同

减法轮先做 **scope subtraction**，再做 **architecture subtraction**。当前 diff 新增的行为不自动成为必须保留的合同；保留边界只来自用户目标、编码前 mini spec/RFC 当前切片和 base 已有兼容行为。

减法轮必须在 correctness 和开放轮 finding 之前单独交付以下五项：

1. **Scope ledger：** 把每个新增 production behavior、文件和测试组映射到用户目标或当前 RFC/mini spec 的明确 merge condition；无法映射的项标记 `DELETE / DEFER`，并恢复 base 行为。不能用“当前测试依赖”“顺便修好”或 PR body 已经宣传该行为作为保留理由。多 PR RFC 只允许当前切片进入后续 census。
2. **当前 census：** 只对 scope ledger 保留的实现枚举新增或扩张的 production helper、class、field group、allowlist、owner projection、跨层中间 artifact 和末端补偿流程；相同文件里的多个对象不能合并成“一个模块”跳过。普通局部变量、只为一次循环组织数据的 tuple/dict 和无语义分支的表达式不单独计 abstraction，除非它们承担 owner、projection、precedence 或 lifecycle 边界。
3. **最小设计：** 在完整实现当前授权目标、同时保持 scope 外 base 行为不变的前提下，写出最少需要的 owner artifact、转换和 consumer。不得删减用户目标；也不得把当前 diff 未获授权的新行为伪装成兼容合同。
4. **逐项减法账本：** 对 census 每一项标记 `KEEP / INLINE / MERGE / MOVE / DELETE`，给出当前代码锚点和理由。`INLINE` 必须删除 callable、独立分支或 owner 边界，内联局部变量不算；`MOVE` 只有复用已有 owner 并同时删除旧 owner 或重复流程才算。换文件、改名、少一个临时变量或再包一层都不算减法。
5. **净结果：** 先报告 scope subtraction 删除的行为、production 文件和测试组，再报告 architecture subtraction 中 abstraction、owner、重复 projection、末端补偿和 production 分支分别净减少多少。行数只作佐证，不能用删注释或格式变化充数。

减法轮的 `PASS` 只有两种：先证明 scope ledger 没有未授权行为，再给出可执行的删除/合并/内联方案；或逐项证明保留范围和当前 census 已分别等于授权 scope 与最小设计。只报告字段丢失、入口绕过、错误优先级、未知字段未拒绝等 correctness bug，即使都是真的，也算减法轮 `FAIL`；这些 finding 留到后续轮次。用于验证知识规则是否生效的已知 scope-creep 样例，如果 reviewer 只删局部 helper、没有提出删除整块未授权行为及其测试，规则实验必须判 `FAIL`。

### Source-consumer decision matrix

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
