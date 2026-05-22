---
name: review_delegation_framing
description: When spawning review sub-agents, don't pre-narrow their scope with your own hypothesis — that inherits your bias. Open-ended audit, or parallel multi-framing union.
metadata:
  type: feedback
---

Spawn review sub-agent 时**禁止把自己的 hypothesis / focus 塞进 prompt**。

**Why:** sub-agent 没有我的上下文 ≠ 没有偏见——偏见**通过我给它的 prompt 传染过去**。子 agent 严格在 prompt 框定的范围内审查，框外的问题它压根不看。

**实测**：用户提示"类似 reviewer 之前指出的问题"，我直接搬给 review 子 agent，它围着那个 framing 找，捞到了同类问题，但完全没去 audit：
- API rename 残留（旧名还留在 e2e test）
- producer→consumer signature 完整性（新字段在 producer 加了，但 consumer 第三参没填）

独立触发的第二个 review（没我的 framing），反而把这两类都抓到了。

**How to apply:**

❌ 错的 prompt：
- "review 这个 PR，特别是 X / 类似 Y 的问题"
- "重点查 hardcoding"
- "复用上次 review 的 action list 再扫一遍"

✅ 对的 prompt：
- 开放式："静态 review 这个 PR，列你认为需要改的所有问题，分级 P0/P1/P2，不要预设焦点"
- **并行多 framing union**：同一 PR 起 3 个子 agent
  - agent A：API 一致性（rename / 旧名残留 / cross-product grep）
  - agent B：producer↔consumer signature 完整性（每个新字段从写入处 trace 到读取处）
  - agent C：测试覆盖（每个新 code path 是否有 test，已有 test 是否还能覆盖）
  - 各跑各的，最后 union 结果
