---
name: debug-funnel-discipline
description: 调试漏斗纪律：grep 优先于实测、怀疑收敛到 1 个再动手、user 给诊断 ≠ user 给修法、多层报错抓深层不抓表层、framework 错误前 sanity check tensor 形状
metadata:
  type: feedback
---

# 调试漏斗纪律

多次 bug 复盘：相同 bug 用静态分析路径 10 分钟搞定，用实测循环路径 2h 仍未定位。

| | 我（错） | 正确路径 |
|---|---|---|
| 总耗时 | ~2h | ~10min |
| 远端启停次数 | 4 次（每次 ~2min model load）| 0 |
| 怀疑点 | 同时持有 5 个，每个都跑实测 | 收敛到 1 个，静态读 3 个文件 |
| 真因发现路径 | 改了 4 处代码全部 revert，才回到起点，再静态找 | 静态读调用链 → 找到配置字段不一致 |

派生自 [P1 证据先行] + [P4 单变量隔离归因] + [B29 用户给 fix 指令直接动手] 的反向场景。

---

## 规则

**触发器**：debug bug 时同时持有 ≥2 个独立怀疑，或想 "重启服务跑一次试试"

**强制**：

### (a) grep 优先于实测

| 动作 | 成本 | 信息量 |
|---|---|---|
| 启动 server + 1 次实测 | ~2-3 min | 1 个 hypothesis 的 yes/no |
| `grep -rn <symbol> <dir>` | <1s | 全文件分布 |
| 读完整调用链（4 个文件 × 50 行）| ~3 min | 整条 path 的所有 fork 点 |

**规则**：连续 ≥2 次实测仍未定位 → **强制回静态**，禁止再启动服务，直到找到新的怀疑点。

### (b) 怀疑收敛到 1 个再动手

**禁止**：同时持有 ≥2 个独立怀疑时动手 fix 任何一个。

**强制流程**：
1. 列出所有怀疑点
2. 标相对概率排序（基于 grep 出的实际代码分支多少 / 配置字段是否真存在 / 历史 commit 是否动过）
3. 静态二分排除：每个怀疑找一个**便宜的反证**（grep 一行能否证伪）
4. 收敛到 1 个 → 动手 fix
5. 不能收敛 → AskUserQuestion 让 user 给方向，**禁脑补**

**Why**：N 个怀疑里只有 1 个真，先 fix 错的 (N-1)/N 概率 = 80%（N=5）需要回滚的修改。4 处全改全 revert 印证。

### (c) user 给诊断 ≠ user 给修法

| user 说 | 我应该做 |
|---|---|
| "改 X 文件的 Y 函数加 Z 参数" | **直接动手**（B29 适用）|
| "这个函数没有覆盖某个场景" | **先 framing 修法 scope**：是改这个函数 / 周边 / 还是别的层？AskUserQuestion 给 ≤3 个修法选项 |
| "之前修好了，现在又出来了" | **先 trace timeline**：什么时候修的、什么时候坏的，**禁猜测立刻改代码** |

**禁**：基于 user 单句诊断脑补"按真值表改函数 + 加参数 + 改多处 call site"——这是**修法范围 inflation**，B29 不适用。

---

## 信号识别

- 列怀疑点超过 2 个，每个想"试试"
- 想"重启 server 验证一下" → 先问：能不能 grep 出答案？
- 想"按 X 修一下试试" → 先问：诊断闭环了吗？
- 想"等用户给方向" → 先问：我的 grep 做完了吗？
- 修改 ≥3 个文件后才发现方向不对要 revert → 早期没收敛信号

---

## 静态 debug 路径示例

**bug 现象**：online 路径输出 A，offline 同 prompt 输出 B（systematic 偏差）。

**错误路径**：
1. 猜测 stop 差异 → 加参数 + 2 处 call site → 跑 → 行为没变 → revert
2. 猜测另一个字段 inject → 加 guard → 跑 → 输出完全一样 → revert
3. 加 PROBE 打内部值 → 跑 → 看起来正常 → 死路

**正确路径（静态）**：
1. grep 两条路径各自的 stop/config 设置逻辑
2. 读 offline 路径："对所有 tokenizer-owning stage 覆盖参数"
3. 读 online 路径："找 `is_tokenizer_stage: true` 的 stage"
4. 看配置文件：`is_tokenizer_stage: false` → online 找不到 → 参数不覆盖 → 钉死

**修法**：配置文件改一行 + 6 行注释。1 文件 7 行。

---

## torch.compile / dynamic shape 类报错的额外规则

### (d) 多层报错信息抓深层不抓表层

torch.compile / dynamo / 类型推断报错经常有两层：
- 表层："X 和 Y 关系错"（命名两个具体 entity）
- 深层："某个声明被某段代码烤成常量 N"（指向声明配置 / 调用代码哪里坏了）

**规则**：报错里出现"specialized to constant N" / "marked dynamic but ... constant"，先 trace N 是哪来的（一般是某个 yaml config / max size），从那条链反推**哪个 dim 在源头标错**。**禁**先做"让 X == Y 在运行时成立"的 runtime check——那是表层 fix。

### (e) framework 错误前先 sanity check tensor 真实形状

调 torch.compile / fx / dynamo 错误前，先确认每个被命名 tensor 的 runtime shape，**不**按"标准 LLM tensor shape 约定"假设。多模态模型经常打破"dim 0 = num_tokens"约定。

**规则**：torch.compile 报错前问 3 件事：
1. 这些 tensor 的 runtime shape 是什么？（不是看类型注解，看实际 forward 调用方）
2. 装饰器自动推断的 dynamic dim 跟实际 shape 哪一维是变长维一致吗？
3. 兄弟模型（同 attention family / 同模态架构）的 `@support_torch_compile` 调用模板是什么？

**失败模式示例**：
- 抓第一行"两个 size 不一致"→ 想在 runtime 把它们对齐（表层 fix）
- 没看数据，按"标准 LLM tensor shape 约定"假设 positions 是 1D
- 找到相似例子就抄，没想自己 tensor shape 跟例子不同（比如 multi-modal 的 positions 是 2D）

---

## How to apply

**debug 开始时**：
1. 列怀疑点 + 相对概率
2. 看每个怀疑点能不能 1 行 grep 证伪
3. 二分到 ≤1 个再动手

**实测之前自审**：
- 我现在多少个未排除候选？≥2 个 → 停，回去 grep
- 上次实测验证了哪个 hypothesis？答不上来 → 那次实测白跑

**user 说话后自审**：
- user 说的是现象 / 诊断 / 修法？
  - 现象 → 我去 trace
  - 诊断 → 我先 framing 修法 scope（AskUserQuestion），别脑补
  - 修法 → 直接动手（B29）

---

## 链接

- 上位原则：P1（证据先行）、P4（单变量隔离）
- 相邻：[execution_principles](execution_principles.md)（用户给方案直接执行）、[conclusion_discipline](conclusion_discipline.md)（推理 vs 实测前缀）
- 反向：[B29] user 给具体 fix 指令禁 detour（这条管的是给 fix 指令的场景，本规则管诊断不给 fix 的场景）
- 派生硬规则：CLAUDE.md B32
