---
name: algorithm-vs-framework-fix
description: framework 层 patch 和 algorithm 层 fix 都能解释同一观察现象时 default to algorithm fix；用 framework hack 兜底 algorithm 错是 cargo-cult
metadata:
  type: feedback
---

# Framework hack vs algorithm fix

多阶段推理 pipeline 调试中反复出现：两套描述 fit 同一现象（"pipeline 跑过头"既能从 algorithm 层解释也能从 framework 层"补 cap 机制"打补丁），**两次选了 framework hack 路线**，每次都被 reviewer 拉回 algorithm 路线。

派生自 [[P3 完整链路而非单点]]。

---

## 规则

**触发器**：观察到 framework 层"少一个机制"（cap 缺、orchestrator 没 defer、配置没覆盖参数、middleware 没 cleanup hook ...）

**强制（决策顺序）**：
1. **先问 algorithm 层**：是不是上层在产生不该有的状态？让上层别产生 → framework 自然不用补
2. 才考虑 framework 加机制：上层确实需要这个状态，framework 缺一个合理 API

**禁止**：
- 跳过 step 1 直接加 framework 机制
- "algorithm 层 owner 在另一个团队，framework 这边补一下" → 跨团队不是借口；同一 PR scope 内能改 algorithm 就改
- 多个 framework hack 串起来兜底一个 algorithm 错（symptom：3 个独立的 hack 都"必须放在一起才 work"——这是 cargo cult 复合）

---

## 信号识别

**framework hack 在补 algorithm 错的特征**：

| 信号 | 解释 |
|---|---|
| hack 的注释里出现 "为了应付 X 这种特殊情况" | X 是 algorithm 层故意 / 意外的产物 |
| hack 触发条件复杂（`if A and not B and stage_id != C`）| 在精确匹配 algorithm 层错误产生的 narrow state |
| hack 之间互相依赖（hack1 在配置文件，hack2 在调度器，hack3 在 bridge 层）| 没有上层 algorithm 改动能一处吃掉 |
| 加 hack 后还要加 "extra check" 防 hack 本身崩 | hack 制造了新失败模式 |

---

## Why（实测案例）

**症状**：多阶段 pipeline 中，stage A 结束点配置错误（应在 token X 停，实际在 token Y 停），导致：
- 多余 KV / hidden state 被 emit 出来（S-N 偏高）
- stage A mid-decode 时 ready 信号就 fire，下游消费时数据不完整 → crash

**framework hack 方案（三件套）**：
1. 配置文件加 `transfer_criteria: token_id=X, stop_after_transfer=false`
2. 调度器加 defer，等 stage A finish 才 forward partial output
3. stop 参数改成宽松值让 stage A 走完 forced tail

三件套互相依赖——任何一个单独抽掉都不 work。

**algorithm 路线（reviewer 指向后揭示）**：
- stage A stop 直接设到正确 token range
- stage A 自然停在 token X → KV 自然 cap → S-N=1
- 自然 finish → 没有 mid-decode ready → 调度器不用 defer
- 三件套全消，配置文件改一行

**净结果**：删配置 block 20 行 + 删调度器 defer 14 行 + 改 stop algorithm 30 行。一处 algorithm fix 吃掉三处 framework hack。

---

## How to apply

**调试时遇到"framework 少机制"的判断分支**：

```
现象 = framework 层补丁 OR algorithm 层 fix
    ↓
先问：algorithm 层能不能不产生这个状态？
    ├─ 能 → 改 algorithm（一处吃掉）
    └─ 不能 → 加 framework 机制
       ↓
       这时再问：upstream 怎么处理的？（接 [[upstream_first_for_algorithm]]）
```

**review / 写完 patch 后自检**：

- 我这个 patch 在补什么状态？这个状态是不是上游故意/意外产生的？
- 上游能不能不产生这个状态？
- 如果能：先 revert framework patch，去 fix algorithm
- 跟 [[conclusion_discipline]] 规则 2 联动："harmless 必须有完整因果链" — algorithm 错没修，framework hack 的副作用因果链通常不完整

---

## 反模式

- "我先把 framework 兜住，algorithm 后面再优化" → "后面"永远不会发生
- "yaml 加个配置就能 fix，最小改动" → 改配置看起来小，但配置背后的 framework 路径是不是真的为这个场景设计的？
- "上游也有这个机制" → 检查上游是不是真的用它（很多 framework feature 是 dead code）

---

## 链接

- 相邻：[[conclusion_discipline]] 规则 2（harmless 因果链）
- 相邻：[[upstream_first_for_algorithm]]（去查 upstream 怎么做 algorithm 决策）
- 派生硬规则：CLAUDE.md B31
