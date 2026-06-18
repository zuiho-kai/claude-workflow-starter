---
name: upstream-first-for-algorithm
description: algorithm-level 决策（stop token / sampling 策略 / 特殊 token 处理 / generate loop 行为）前必须先 grep upstream 源码，B7 精神扩展
metadata:
  type: feedback
---

# Algorithm-level 决策前先 grep upstream

多次 PR review 复盘。upstream 源码就在 repo 里，**距离一次 grep 的距离**，没读，靠 trace 现场反推方案，结果跟 upstream 设计哲学背道而驰。reviewer 一句"ref upstream line N"把方案打回原形。

派生自 [[P1 证据先行]]。是 [B7] 的精神扩展——B7 字面只管"测 baseline 前 grep README"，这条把它扩到所有 algorithm 决策。

---

## 规则

**触发器**：准备做以下任一类决策
- stop token / EOS / sampling 策略选择
- 特殊 token（control token / placeholder / trigger tag）处理
- generate loop 行为（forced emission / logits processor / stage transition）
- scheduler / denoising loop / prediction type / step spacing
- timestep / positional embedding basis and order
- activation function or gated-MLP detail
- token / joint / latent / image / action ordering
- attention mask, pad/eos, and special-token semantics
- preprocess / resize / mask / coordinate transform / normalization
- KV cache 切片 / snapshot 触发点 / reuse 长度
- prompt 模板 / chat_template / system prompt 注入位置

**强制**：
1. `find $UPSTREAM_REPO -name "modeling_*.py" -o -name "generation_*.py" -o -name "tokenization_*.py"` 找主入口文件
2. grep 关键概念名（`stop_tokens` / `EOS_TOKEN_ID` / `stage_transitions` / `apply_chat_template` 等）
3. **读完相关函数体**才动手设计

**禁止**：
- 靠"观察 token 序列 + 反推" 自己造 algorithm 方案
- 把 upstream 当"备查参考"而不是"先验证设计"
- 已经 clone 的 upstream repo 当透明（README 提过的、CLAUDE.md 提过的 reference repo）

---

## Why（实测）

发现 stage A stop 太早砍掉某个 tail → 直接换成宽松 stop token，理由"让 stage A 走完 forced tail 直到自然 EOS"。

**upstream 实际做法**：stop 在特定 token 本身，配 logits processor 强制下一个 token 落到正确区间。stage A 的自然轨迹在某个 control token 处就终止。

我的方案让 stage A 白跑 5 个额外 decode step。reviewer 第一条 review 直接戳穿："ref upstream line N and run comparative experiment"。

---

## How to apply

**改 prompt_utils / sampling / stop tokens 前**：

```bash
grep -rn "stop_token\|EOS\|eos_token_id" $UPSTREAM_REPO/modeling_*.py | head
```

**改 KV cache 切片 / snapshot 前**：

```bash
grep -rn "kv_cache\|snapshot\|reuse_len" $UPSTREAM_REPO/modeling_*.py | head
```

找不到 / 不存在 → 才推理。能 grep 出来 → **必读再动**。

---

## 反模式

- "我 trace 现场就够了" → 看不到 upstream 的设计 invariant
- "等 reviewer 提了再改" → reviewer 不是 oracle，upstream 才是
- "upstream 太复杂，先按自己理解写" → 永远不会回去对 upstream，diff 越走越远

---

## "Upstream" 包含本仓库内的同类工具类

**触发**：加 utility / helper / 纯 Python 复刻**前**。

**强制 grep**：`grep -rn "<同名函数或同概念>" src/ <upstream_repo>/`，**两边都查**。仓库里已有的同类 Processor / Sampler / Group 等**就是 upstream**——它们已经把上游算法对齐过一次了，再写第三份纯 Python 复刻 = 三处需要同步的源码漂移。

**实测**：我加了 `_build_reso_group_ratios`，仓库里已有两处同概念实现。reviewer 一句"可以复用吗？"直接戳穿。

"模块标 lightweight / no-torch 所以不能 reuse" 不是借口：算法可以**移到持有数据的那一层**，重 import 在那一层本来就 OK。约束应该指向"在哪做"，不应该被偷换成"再造一份"。

**派生规则**：加工具函数前必跑：
```bash
grep -rn "<algorithm-name>|<key-concept>" src/ scripts/
grep -rn "<algorithm-name>|<key-concept>" <upstream_repo>/
```
**两边都返回非空 → 必须先回答"为什么不 reuse"再动笔**。

---

## Shape-compatible semantic bugs 也是 algorithm bugs

新模型或新 pipeline 接入时，shape clean、strict load、stub smoke 都通过，不代表语义对齐。以下字段经常不会立刻 crash，但会让模型行为偏掉：

| Field | Common false comfort | Upstream check |
| --- | --- | --- |
| timestep / positional embedding | 维度对就行 | basis、`cos/sin` 顺序、scale |
| activation | MLP shape 一样就行 | GELU/tanh GELU/SiLU/gated variant |
| token or latent order | concat 后长度一样就行 | time/frequency/state/action/image/latent order |
| scheduler | 能循环去噪就行 | prediction type、solver、step spacing |
| attention mask | `input_ids != pad_id` 是通用写法 | `pad_id == eos_id`、special token 是否参与 attention |
| preprocess | dtype/shape 对就行 | resize、crop、mask、coordinate system、normalization range |

如果代码在复刻 upstream module，必须 diff 这些 semantic fields。找不到上游实现时，明确标成 source inference，不要写成已经验证。

---

## 链接

- 相邻：[[reviewer_lens_audit]]（duplication audit 章节）
- 派生硬规则：CLAUDE.md B30
