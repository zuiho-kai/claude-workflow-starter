---
name: reviewer-lens-audit
description: 自审 / sub-agent review 必跑的 4 条 reviewer-perspective audit。Sub-agent 说"OK"是弱信号——它只会答你问的那个问题。
metadata:
  type: feedback
---

# Reviewer-lens audit：4 条必跑清单

**Why：** 某次 push 前让 sub-agent code check 说"no problem"，reviewer 一上来 4 条评论：算法重复 3 份、resolution 算在错的层、token id 非连续段没处理、help text 冗余。**用户原话："这是严重问题，你要学习从 review 角度去看问题。code check 他护不住，容易被打回。"**

派生自 [[review_delegation_framing]]——那条管"怎么 spawn"，**这条管"必须审什么"**。CLAUDE.md B33 是硬规则入口。

---

## 🚫 禁用 framing（这些 prompt 直接换掉）

下列任意一句 = 子 agent 必答 "no issues found / looks OK"，**护不住** reviewer：

- "帮我 code check 一下"
- "看有没有问题"
- "review 一下这个 PR / commit / 改动"
- "static review 看下"
- "扫一遍" / "审一下"
- "确认一下没问题"

**Why**：子 agent 严格在 prompt 框定的范围内答；没给 audit 维度 = 它没有判定 "出问题" 的标尺，默认走"看起来合理就 OK"。

**替换**：用下面的 4-audit 模板，或把模板拆 3 份并行（duplication / layering / edge+surface）。

---

## ✅ Sub-agent prompt 模板（直接粘贴用）

```
Static review this PR/diff/change. For EACH of the four audits below, return
findings (P0 blocker / P1 should-fix / P2 nit) OR explicitly write "none found"
— do not skip any audit and do not pre-focus on one over another.

# Audit 1 — Duplication
Grep both the repo (src/, scripts/, etc.) and the upstream reference
repo for functions / classes / algorithms / constants that overlap with anything
new in this PR. List each match with:
  - file:line of the existing implementation
  - file:line of the new implementation
  - 1-line judgment: should reuse / cannot reuse + why

# Audit 2 — Layering
For each new piece of logic, identify which module persistently holds the data
it operates on. If logic and data live in different modules (e.g. resolution
done in CLI/serving but data in Processor), list as a finding with:
  - new logic location
  - data owner location
  - proposed correct home

# Audit 3 — Edge cases
List every range / boundary / default value the new code touches. For each,
name which branches handle:
  - empty / single-element / max-size extremes
  - non-contiguous ID ranges, off-by-one (range(s, e) vs s..e inclusive)
  - None vs 0 vs sentinel (which branch does "not provided" take?)
Flag any boundary not explicitly handled.

# Audit 4 — Surface area
List every new public knob (CLI arg / API field / extra_args key / config
option / new public function). For each, answer:
  - Can it be derived from existing knobs? If yes, why expose it?
  - Why is the default what it is? Can the help text be shorter?
  - Is the same value also expressible via another path (CLI vs env vs config)?
  - If this is an internal optional fast-path parameter, what are its data
    contract and execution-context contract, and where does a wrong caller fail?
Flag knobs that are accreted/over-defensive.

Return findings in markdown. End with one line: "AUDITS RUN: 1,2,3,4 — N findings (Pa P0, Pb P1, Pc P2)".
```

---

## 规则

**触发**：自己 push 前 + spawn review sub-agent 时。

**Sub-agent OK ≠ clean PR**。子 agent 只严格在 prompt 框定的范围内审，**没问到的它不会主动说**。每次开 PR / 自审都必须显式跑这 4 条 audit，不论自己跑还是 union sub-agent。

### Inline review 处理：锚点代码是 source of truth

处理 GitHub inline review 时，**评论文字不是唯一输入，锚点代码才是 source of truth**。每条评论动手前必须先写出 action mapping：

```text
Comment: <reviewer 原文>
Anchor: <file:line + 锚点代码实际行为>
Pronoun target: <this / it / here / strategy 指向锚点里的哪个实体>
Reviewer asks: <按锚点语义拆成 1-3 个具体要求>
Code action: <要改哪个 owner/module，什么逻辑从哪里移到哪里>
Done check: <回到锚点附近看 diff，reviewer 是否会认为正面解决>
```

**禁止按关键词修评论。** 看到 "image processor" 不等于随便搬一个相关 helper；看到 "add comments" 不等于只加 docstring。先问：reviewer 评论锚在哪几行？这些行的行为是什么？`it` / `this` / `strategy` 默认指锚点里的最近代码实体，而不是上一条评论、相邻概念、或自己脑中相关的模块。

**反例**：reviewer 锚在某个 postprocess resize 函数上，评论说"Add comments to explain the alignment strategy and also add it to image processor?"。第一次只把另一个相关 helper 搬进 processor + 给原函数加 docstring，是**按关键词修**，没有按锚点修。正确 action mapping 应该是：把 output alignment strategy 整体放到 Processor，pipeline 只调用 processor method。

**Done check**：改完必须回到原评论锚点附近看 diff。如果锚点附近的核心逻辑仍留在原 owner，只是旁边多了注释或改了相邻 helper，不能算完成。

### Audit #1：Duplication（已经有了吗？）

新增的函数 / class / 算法 / 常量，**先 grep 仓库 + 已 clone 的 reference repo**，看有没有同概念实现：

```bash
grep -rn "<function-name-or-concept>" src/ scripts/ <upstream_repo>/
```

返回非空 → 必须答"为什么不 reuse"，写不出答案就 reuse。

**典型信号**：你的新函数名跟某处现有函数 80% 重合、algorithm 描述能完整复刻另一处的 docstring、参数列表镜像现有 class method。

### Audit #2：Layering（这逻辑住对地方了吗？）

新逻辑需要的数据 / 状态在哪持有？**逻辑就该在哪**。

- entry point（CLI / serving 层）做了本该在 model / processor 里做的解析 → 错层
- 把数据序列化成"不透明 token"传给下游 → 信号：下游需要的不是这个 token，是原始数据
- "lightweight 模块不能依赖 heavy 模块"是真约束，但解法是**把代码搬到 heavy 模块那一层**，不是**在 lightweight 模块再造一份**
- generic helper 的参数名带着某个 caller 的专有概念 → helper 抽象层级和命名层级不一致

**问自己**：把这段代码 cut，paste 到 X 模块里能不能直接跑？能跑就该住那。

### Audit #3：Edge cases（非连续 / 边界 / off-by-one）

这是 reviewer 不会明说但会指出 bug 的地方。**主动查**：

- 看起来连续的 ID range 真的连续吗？（某段 token id 有两段不连续区间，一个 `start + idx` 的算式覆盖不了）
- 默认值 None vs 0 vs sentinel 的边界（"没传"和"传了 0"哪个走哪条分支）
- list / set / range 的 ±1 边界（`range(s, e)` 含 s 不含 e，`s..e` 通常含两端）
- empty / single-element / max-size 三个极端

不写 test 不要紧，但**必须在 commit message 或 review 自答里点名**这几个边界走了哪条分支。

### Audit #4：Surface area（这个 knob 真的必要吗？）

新增的 CLI arg / API 字段 / extra_args key / 配置项——**问**：

- help text 在解释什么不该解释的事（"defaults to X for case A, Y for case B"）→ 信号：默认值本来就是 caller 算好的，不该再让 user 指定
- 参数能从另一个参数派生 → 不该独立暴露
- 多个 enum knob 互斥但都暴露了 → 应该合并 / 用一个判别字段
- 内部方法新增 optional fast-path 参数也要当 surface area 审：docstring 是否写清 device / contiguous / shape / length / ownership / `None` fallback contract
- optional tensor/cache/staged/buffer 参数要拆两张 contract：
  - data contract：device、dtype、shape、contiguous、长度、detach/lifetime，由数据 owner 校验
  - execution-context contract：rank、stage、mode、stream、cache enabled 状态，由知道上下文的 caller owner 校验
- 新增 optional 参数不能靠"现在只有一个 caller"保证安全；wrong caller 必须在 owner 边界早炸，而不是 silent fallback 或晚点产出错 payload

**反模式**：加 knob 是 cheap，删 knob 是 breaking change。**默认不加**，等 user 真的提需求再加。

### Streaming / API protocol audit（新增 stream/SSE/WebSocket 必跑）

新增 `stream` 参数、SSE chunk、WebSocket message、OpenAI-compatible response schema 时，把它当 public protocol surface，不要当内部 helper：

- 先 grep 仓库已有 streaming endpoint，逐项对齐 `normal chunk / validation error / EngineDeadError / generic exception / client disconnect / DONE` 行为；尤其 engine-dead 不能被 generic `except Exception` 吞掉。
- structured error 不能降级成裸字符串异常；`ErrorResponse` / `HTTPException` 的 status、type、code 必须能一路进 error chunk。
- 字段名叫 `delta` 就必须可 append；测试要模拟客户端把所有 delta 拼起来，断言最终文本/音频/状态正确。若支持 replacement，协议要显式表达 `full_text` / `reset` / snapshot，不要继续叫 delta。
- `[DONE]` 是协议事件，不是 finally 里的装饰；确认 error 后、empty final output、client cancel、engine-dead 各分支是否应该发，以及发几次。
- 新 streaming 路径不要只测 `200 text/event-stream`；至少补一个 4xx preservation、一个 engine-dead/shutdown、一个客户端重建状态测试。

---

## How to apply

### 自审（push 前）

逐条对照 4 项写 review note，不要心算"应该没问题"。**reviewer 第一眼看到的，自己第一眼也得看到**。每跑一项在 commit message 或 PR description 显式标 "AUDITS: 1✓2✓3✓4✓"。

### Sub-agent review（spawn 时）

用上面 **"✅ Sub-agent prompt 模板"** 那段——逐字粘贴。不要省略 "AUDITS RUN: 1,2,3,4 — N findings" 那行尾签——它强制子 agent 自检确实跑了 4 项，缺项就要补跑。

### 并行 multi-framing union（更稳）

3 个 sub-agent 各跑一项（duplication / layering / edge+surface），结果 union。比单 agent 全跑更难漏：

```
Agent A prompt: 只跑上面模板的 Audit 1（Duplication）。返回 finding 或 "none found"，
                 不要做其他维度。
Agent B prompt: 只跑 Audit 2（Layering）。同上。
Agent C prompt: 跑 Audit 3 + 4（Edge cases + Surface area）。同上。
```

收回三份结果**自己 union**，不要再 spawn 一个"汇总 agent"——那会再过一层 framing 漏斗。

---

## 反模式

- "sub-agent 说 OK 我就 push 了" → 子 agent 只答你问的，没问的不会说
- "我先 grep 过了" 但只 grep 了一处（仓库 OR upstream，不是 AND）
- 把 audit 当 "可选 thoroughness"，赶时间就跳——reviewer 永远不会跳，跳的代价是 review iteration
- "我 commit message 写了 trade-off" 但**没写边界条件**——trade-off 是设计选择，边界是 bug 入口

---

## Where this came up

- 某次 fix/image-size PR：reviewer 4 条评论同根因（duplication + layering），sub-agent code check 全程说 OK。
- 用户：「我之前让子 task code check 他说没问题」「这是严重问题，你要学习从 review 角度去看问题」
- 某次 prefix-cache CPU staging PR：code check 无 P0/P1，但抓到三个 reviewer 视角问题：新增参数 docstring 没写 CPU/contiguous/length contract；generic helper 参数名泄漏 hidden-state caller 语义；只审了 data contract，漏审 execution-context contract（wrong caller 要早炸）。
- 某次 streaming endpoint PR：happy path tests + lint 过，但 review 抓到 EngineDeadError 被 generic SSE error 吞掉、ErrorResponse 400 被 ValueError 降级成 500、delta replacement 不满足 append 语义。

---

## 链接

- spawn 子 agent 怎么写 prompt（避免偏见传染）：[[review_delegation_framing]]
- duplication audit 的具体派生：[[upstream_first_for_algorithm]]（in-repo equivalents 章节）
