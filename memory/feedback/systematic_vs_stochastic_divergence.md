---
name: systematic_vs_stochastic_divergence
description: When two code paths produce different outputs on the same model, the FIRST move is to classify "systematic" vs "stochastic". Don't invoke CUDA/MoE non-determinism for cross-path bias — the real cause is usually a silent upstream input difference (e.g. PIL Image alpha-channel mismatch). Don't repeat.
type: feedback
---

When user reports "path A consistently produces X, path B consistently produces Y" on the same model with the same seed:

## Rule 1: Systematic ≠ stochastic. Classify first.

| Signal | Class | First-line investigation |
|---|---|---|
| "X every time on A, Y every time on B" (cross-path bias) | **Systematic** | Diff inputs to the model byte-by-byte. The two paths must be feeding different inputs. |
| "X then Y then Z on same path same seed" (within-path drift) | **Stochastic** | CUDA non-determinism / MoE BF16 / scheduler timing. Different fix class (deterministic mode, etc.). |
| Both | Both | Treat as systematic FIRST. Stochastic on top is a separate concern. |

**Why:** "CUDA / MoE non-determinism" is a tempting last-resort explanation for cross-path bias because (a) it's a known real thing for some models, and (b) it sounds technical. But it explains **noise within a path**, not **systematic bias between paths**. If you invoke it for cross-path bias you're projecting a known phenomenon onto an unrelated bug.

## Rule 2: Model input is 3 pillars, not 1.

For a multimodal model, the model receives:

1. **Text token IDs** (tokenized prompt string)
2. **Multimodal data** (PIL images → preprocessor → tensors)
3. **Sampling params** (seed, temperature, top_k, max_tokens, stop_tokens, ...)

Aligning pillar 1 byte-for-byte across paths does **NOT** mean the model sees identical input. Pillar 2 and 3 must also be byte-equivalent. A common miss: pillar 1 was byte-identical between two paths but pillar 2 differed (RGBA composited over white vs over black) → model saw two different image tensors → different outputs.

**How to apply:**

```
For each model input pillar, dump from both paths and diff:
  - token_ids   (post-tokenize)
  - multi_modal_data["image"] -> processor -> tensor (compare byte-wise)
  - sampling_params (compare repr())
```

If pillar 1 matches but pillar 2 diverges, the upstream-of-model preprocessing is the bug.

## Rule 3: PIL Image mode is a silent bug source.

`Image.open(rgba_png)` returns mode RGBA. Different downstream consumers handle the alpha channel differently:

- `.convert("RGB")` composites transparent pixels over **black**
- Some processors composite over **white**
- Some processors pass RGBA through and the model sees 4-channel input

An image with many transparent pixels can produce two completely different RGB tensors depending on which alpha-compositing convention the path uses — enough to make model outputs diverge systematically.

**How to apply:** When two paths consume the same image, check the PIL mode of the input AND look at how each processor handles alpha. If you spot `.convert("RGB")` on one side and an alpha-composite on the other, that's the bug.

## Rule 4: Don't accept "good enough" when user says "still wrong".

If you apply a fix and the symptom partially improves but doesn't fully go away, **keep digging**. Don't escalate to "this is inherent" until you've enumerated every layer.

**How to apply:**
- After each fix, restate the symptom in the user's words and ask "does this fix explain the symptom?"
- If the answer is "partial" or "I'm not sure", treat it as "no" and keep enumerating.
- "CUDA non-determinism" / "inherent characteristic" is the LAST hypothesis to accept, not the first.

## Rule 5: When the user gives a symptom that uses the word "一直/consistently/always", the answer is NOT stochastic.

"一直复现" is a strong signal of **deterministic systematic** divergence. The right reaction is: "what's the same in every run on path A that's not in any run on path B? something on the path must always trigger differently."

## Cross-references

- CLAUDE.md B12 (style/quality bias 类 bug 先静态 diff)
- CLAUDE.md B14 (prior session 的"X 已证伪"标记只对具体 hypothesis 成立)
- CLAUDE.md B20 (输出尺寸/语义异常按 prompt → 中间层 → 最终输出逐层 trace)
- CLAUDE.md P3 (完整链路而非单点)
