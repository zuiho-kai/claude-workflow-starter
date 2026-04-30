---
name: feedback_pr_test_path_audit
description: 审计"已经测过的 PR 还有 bug"时，看 PR 测试实际跑了哪条 code path、用了什么 sampling 模式
type: feedback
---

## 触发条件

- 用户说"之前 PR #N 已经验证过了，但是还有问题"
- 或自己接手发现某条已合并的 example/接口在 greedy 下崩坏，但 PR 描述说"已对齐 HF"

## 不要做

不要直接相信 PR 描述里"已对齐 / 已通过"的字样，直接埋头改代码或重新写测。

## 要做（这次的实证流程）

1. **打开 PR 的"Test Plan"段，逐条问**：
   - 跑的什么 modality / mode（T2T / I2T / IT2I / T2I）？
   - 用 greedy 还是 sampling？yaml 默认 `temperature` 是多少？
   - 有没有和 HF baseline 文本逐字 diff？还是只看视觉/前 N token？
   - 有没有走端到端 string-prompt 路径？还是塞了手工 input_ids？

2. **找 PR 没覆盖的组合**：
   - 别人测了 IT2I sampling + 看图 → 你跑 T2T greedy + 看 AR 文本
   - 别人测了 forward pass（直接喂 input_ids）→ 你跑 `build_prompt(...)` 端到端
   - 别人比对了 first-30-token → 你看后面几百 token（死循环 / 重复都在后段才显现）

3. **挑能让 bug 自暴露的最小用例**：greedy 是 prompt 格式 bug 的 canary——sampling 会把错路径的概率分散，看不出问题。

## 实证（HunyuanImage3 PR #2713 + #3107 + #2986）

| PR | 声称 | 实际测试路径 | 漏的场景 |
|---|---|---|---|
| #2713 | 加 AR 支持，input_ids 已对齐 6364 tokens | 把 HF `prepare_model_inputs` 的 input_ids 直接塞 vllm-omni → first 30 token 对齐 | 没走 `build_prompt(prompt_str)` → vllm BPE 这条路，没看 30 token 之后 |
| #3107 | 加 `examples/end2end.py` `build_prompt` | `--modality img2img --steps 30 --guidance-scale 5.0 --seed 42` + 对比图片视觉 | 没跑 greedy，没看 AR 文本，没对比 HF baseline；error 被 sampling 随机性掩盖 |
| #2986 | 加 smoke 测试 `test_hunyuanimage3_{i2t,t2i}.py` 走 `build_prompt` | I2T: `assert len(generated_text) > 0`；T2I: 对生成图算 CLIP embedding 余弦相似度 | **断言不检查 AR 文本质量**——死循环 garbage 满足 `len > 0`，IT2I 的 garbage AR 文本也能让 DiT 拼出像样的图（DiT 主要靠 cot_text 关键名词）通过 CLIP 阈值 |

**结果**：T2T greedy 下 `build_prompt(task="t2t")` 直接产出 `massive arches massive arches ...` 死循环，IT2I greedy 死循环 `image_1...` × 7。三个 PR 都路过这段 build_prompt code，但**没有任何一个的断言能让 bug 暴露**：
- #2713 不走 build_prompt 路径
- #3107 用 sampling + 看图片
- #2986 走 build_prompt 但断言只看长度/CLIP，不看 AR 文本结构

## Why

- "已对齐 30 tokens" 不能保证后续不发散——causal attention 让 image embedding 阶段的细微差异传播到 `<think>` 时已被放大
- sampling（temp=0.6 + top_p=0.95）能从 degenerate 模式里"跳出去"产合理输出，掩盖 prompt format bug
- 视觉只看 DiT 出图——AR 文本 garbage 也能让 DiT 拼凑出能看的图（DiT 主要靠 cot_text 的关键名词）

## How to apply

接到"PR 已测但还有问题"的工作，先做 4 件事再动代码：
1. 翻 PR 的 Test Plan 一字一字读
2. 翻**测试断言代码本身**——`assert len > 0` / 视觉相似度 / first-N-token diff 之一基本都漏 prompt 格式 bug
3. 跑同一脚本但用 `temperature=0`（greedy）+ 完整 output 对比 HF
4. 跑同一脚本但走端到端字符串 prompt（不是手工 input_ids）

任何一项产出 garbage，就把那个组合写成回归测试加进 `tests/` 再修代码。

**别忘了 multi-stage pipeline 的 mask 效应**：AR + DiT 的 IT2I/T2I，AR 文本即使是 garbage，DiT 拼出的图也常常能通过 CLIP/视觉相似度阈值（DiT 主要消费 cot_text 的关键名词，结构标签缺失对图无明显影响）。**T2T 是唯一没有 DiT 兜底的纯 AR 任务，也是 prompt 格式 bug 的最强 canary**。
