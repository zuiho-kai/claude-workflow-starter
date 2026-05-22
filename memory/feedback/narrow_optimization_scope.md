---
name: narrow-optimization-scope
description: 调试中发现的"顺手优化"必须分类（PR 主线必需 vs 周边收益）；后者一律延后到独立 PR；F3 派生加强
metadata:
  type: feedback
---

# 调试中"顺手优化"的 scope 纪律

PR 主线开发期间，顺手做了一个"既绕 edge case 又快 10ms 的优化路径"。reviewer 一眼看穿："this isn't necessary for the current PR"。**问题不在优化本身对错，在它跟 PR 主线无关**。

派生自 [[P7 范围自律]]，是 [F3 派生] 加强版。F3 字面"只碰任务直接涉及的代码"管的是**新写代码**；这条管**调试过程中发现的优化机会**。

---

## 规则

**触发器**：调试 / 实现 PR 主线时发现"顺手优化"或"附赠 fix"，准备塞进当前 PR

**强制（分类决策）**：

| 分类 | 判断标准 | 处理 |
|---|---|---|
| **主线必需** | 主线功能不带这个 fix 就不能 work（功能 broken / test fail / runtime crash）| 留在当前 PR |
| **主线无关 / 附赠收益** | 不带这个 fix 主线照常 work，只是某个指标更好（latency / 可读性 / 别处少绕一圈）| **延后到独立 PR**，当前 PR 不带 |

**禁止**：
- commit message 出现 "plus housekeeping" / "顺手 fix 了 X" / "incidentally improves Y"
- "这个优化跟主线相关 because 它们都碰 prompt 处理" → "都碰同一个文件" ≠ "主线必需"
- "已经 trace 到这了，写都写完了不删可惜" → sunk cost fallacy，删
- "未来 PR 谁知道什么时候开" → 不开就开 issue 占位，不夹带

---

## 信号识别

**调试期"顺手优化"的特征**：

- 修主线 bug 时观察到一个**相邻**现象，自己说服自己"也修一下"
- 这个 fix 跟主线 fix 触碰**同一个文件**但**不同函数**
- 写完 commit message 时需要分两段写（"主线：X" + "顺手：Y"）
- reviewer 视角：能独立 review 这个 fix 不依赖主线知识

满足任一 → 强烈信号，应延后。

---

## Why（实测案例）

**主线**：某 pipeline 支持多输入（up to 3 reference items）

**顺手优化**：发现 tokenize 时有 BPE drift（多字节标点处合并 token），导致 KV reuse 的 `positive_reuse_len` 跟实际 cache 长度差几个 token。**修法**：在 bridge 层把 token_ids 透传，下游端直接用 token-id 不重新 encode。

**主线是否需要**：不需要。多输入功能完全可以在不修 BPE drift 的前提下 work；BPE drift 是另一个独立的路径问题。

**reviewer 的话**：
> "This isn't really necessary. The overall latency is only on the order of 0.01s. And if we want to optimize, we should consider things holistically rather than changing just this one place, which reduces readability. In the future, we might directly reuse embeddings or skip this step entirely. I'd suggest removing this from the current PR."

**reviewer 的两条理由**：
1. 优化本身价值有限（0.01s 不痛）
2. **更重要**：right unit of work 是 unified 优化方案，不是 narrow 切一刀；当前 narrow 优化把架构方向锁住

我没看到第二条，因为我 trace 在现场看到问题就想就近修。**reviewer 视角是架构方向**——narrow 优化提前承诺了一个 design 决策，未来 unified 方案得回来撤掉。

---

## How to apply

**调试发现顺手优化时的 3 步审视**：

1. **删了 PR 主线还 work 吗？** work → 不带；不 work → 必需，带
2. **能独立写一份 PR description 不依赖主线吗？** 能 → 独立 PR；不能 → 真的耦合，带
3. **未来更大的 refactor 会不会撤掉这个优化？** 会 → narrow 优化提前 lock-in 方向，独立 PR / 等 refactor

任一答案不利 → **不带**，开 GitHub issue / TODO 占位。

**已经写了想撤的话**：

- 调用侧的优化代码：删
- 底层 primitive（新增的 utility 函数 / 参数）：留着备用，等真正的 refactor PR 接上
- 测试：测 primitive 的留（pin 底层能力），测优化路径的删
- PR description 写一段 "Optimization leftover" 交代清楚：删了什么、留了什么、为什么、给未来 PR 留 hook

---

## 反模式

- "我调试的时候已经把这段代码读熟了，趁热写完" → 热度高的应该是主线，不是周边
- "PR 多带点东西效率高" → reviewer 的认知带宽是常数，PR 多 1 个 unrelated commit 等于 review 时间 ×2
- "我自己开独立 PR 太麻烦" → 麻烦在 narrow 优化的设计审议上，不在 git workflow 上；独立 PR 强制审议是好事
- "现在不修以后忘了" → 开 issue / TODO comment，别夹带

---

## 子规则：删除中的 diff 最小化

**触发器**：从 tuple unpacking / zip args / 函数参数表里删除一个元素

**强制**：剩余元素如果在**原文件**用 one-liner，就保持 one-liner；不要因为元素变少了 trigger "现在能拆 multi-line 看着舒服" 的想法。

**Why**：reviewer 的 diff hunk 应该只显示语义变化（删 X）。把 `for a, b, c, d, e, f in zip(...)` 改成 multi-line 等于在删 1 个元素的 diff 里塞 7 行格式 churn，扩大了 review surface 且模糊了真实意图。

**How to apply**：
- 删元素前先看原文件的格式，删完后保持同款
- ruff-format 不会自动把 5 元素 one-liner 拆成 multi-line（除非超列宽），所以拆就是手动加的噪声
- 不要拿"美观" / "可读性"当借口动既存格式，那是独立 PR 的事

---

## 子规则：主线受阻时禁向旁边 test infra 扩散

**触发器**：主线（PR 的真实 smoke / 单测）卡住，旁边一堆**与本 PR 无关**的 ERROR 看起来"顺手就能修"（test fake stub / 抽象方法缺实现 / fixture 漂移）。

**强制**：先 grep 那些 ERROR 是不是本 PR 引入。不是 → 当作噪音明确报告给用户："X 个 ERROR 是上游 API 漂移 / test-infra drift，与本 PR 无关"，**禁动手 fake stub**。

**Why**：用 `lambda *a, **k: None` 短路抽象方法检查能让 pytest collect 通过，但：
- 把"被 PR 覆盖的真实 path 测试"和"被 stub 屏蔽的 test fake 抽象漂移"混到同一组 commit 里
- reviewer 看到 fake stub commit 必问"为什么这个 PR 要碰 test infra"，等于把 scope 不必要地扩大
- 真正的 test-infra fix 应该独立 PR，让上游漂移修复方案在合适的 reviewer 下审议

**实测**：主线 smoke 卡住时，看到旁边 22 ERROR 全是某个抽象方法漂移，正要给 fake class 加 lambda stub 时被用户"不要 fake 要解决"直接拦下。停手后转回主线，发现真问题是版本不匹配，rebase main 后端到端一次通。

**How to apply**：
1. 主线卡住时第一反应：grep 失败信号确认是不是 PR 引入。不是 → 在 status report 里明说"X 是上游漂移，不在 PR scope"，**不动手**。
2. 看到 "fake stub" / "lambda override abstract method" / "monkeypatch test fixture" 念头时 → 当作 F8 红灯，停下找用户确认。
3. 真正阻塞主线的 test-infra fix（比如本 PR 新增的 test 复用同一个 fake，没 stub 就根本跑不起来）→ 仍然要分类：(a) 主线必需 stub → 1 行最小 patch + 注释链上游 issue；(b) 旁边一堆 unrelated stub → 独立 PR。

---

## 链接

- 上位原则：F3（只碰任务直接涉及的代码）
- 相邻：[[debug_funnel_discipline]]（受阻时回静态，不向外扩散）
- 派生硬规则：CLAUDE.md F8
