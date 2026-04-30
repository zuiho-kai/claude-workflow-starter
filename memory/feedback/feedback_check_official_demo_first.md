---
name: 测任何模型对齐前必先 grep 官方 demo / README，禁止拍脑袋造测试方式
description: 接 HF 模型做 baseline 对比时，必须先用官方推荐 API（README 里的 demo），不要自己用 model.generate() + 拍脑袋的参数组合，否则拿到的"baseline" 跟模型实际跑法不一致，对比毫无意义
type: feedback
---

## 规则

接 HF 模型做对齐 / baseline 对比测试时，**第一步是 grep 仓库的 README + 找 demo 脚本**，照着官方推荐的 API 调用方式跑。

具体动作（按顺序）：
1. `grep -E "demo|example|generate|infer" $REPO/README.md` 找 inference 入口
2. 看官方 demo 用的是 `model.generate()` 还是 `model.generate_image()` / `model.chat()` / 自定义 pipeline
3. 看官方 demo 的关键参数（`bot_task`、`mode`、`use_system_prompt` 等）取值
4. **照搬**这个调用方式跑 baseline——不要替换成"看上去等价"的更简单 API

**Why:** 模型作者会把"正确的解码逻辑"封装进自定义 generate 函数（如 stage_transitions、final_stop_tokens、custom logits_processor），这些**不是 `model.generate()` 默认行为**。直接用 `model.generate()` 拿到的输出跟官方实际跑法可能完全不同——拿来跟 vllm-omni 对比就是错的 baseline。

**How to apply:** 任何"需要跑 HF 模型 baseline 跟 vllm-omni 对比"的场景，第一步都是 grep README 找官方调用入口，照搬。哪怕官方 API 看起来"绕"也要照搬——绕的部分（多个 stage、自定义 logits processor）往往就是模型的真实行为，不能省。

## 实例：HunyuanImage3 think_recaption (2026-04-30)

**踩坑**：要测 omni 的 `is_comprehension=false` 走 think→recaption 流程，跟 HF 对比。

**错误做法**：自己写 `model.generate(bot_task="auto", eos_token_id=[</recaption>, <answer>, <boi>])` 跑出 346 chars 输出，发现跟 omni 的 811 chars (think+recap) 完全对不上，以为"两边设计不同 / 不可比"。

**真相（看官方 README 才知道）**：
- 官方 demo 用的是 `model.generate_image(prompt=..., bot_task="think_recaption", ...)`，**不是** `model.generate()`
- `generate_image()` 内部 (modeling_hunyuan_image_3.py:3237-3320) 把 `bot_task="think_recaption"` 拆成：
  - `first_bot_task = "think"` → `prepare_model_inputs(bot_task="think")` 加 `<think>` prefix
  - `stage_transitions = [(end_of_think_id, [recaption_id])]` → 强制 `</think>` 后 emit `<recaption>`
  - `final_stop_tokens = [end_of_recaption_id]` → emit `</recaption>` 时停
  - 单次 `model.generate(stage_transitions=..., final_stop_tokens=...)`
- **`stage_transitions` 是 HF 自定义 generate 的扩展参数**，omni 的 `_StageTransitionLogitsProcessor` 跟它是同一个机制
- 直接用 `model.generate(bot_task="auto")` **完全绕过了** stage_transitions——拿到的输出是模型"自由生成"的（HF auto 模式跳过 think 直接 recaption），跟官方推荐跑法 + omni 都不可比

**纠正后**：复刻 generate_image 内部 AR 部分（带 stage_transitions + final_stop_tokens）才能正经跟 omni 对比。

**烧的成本**：30+ 分钟（多次重跑 HF baseline）+ 跟用户解释"两边设计不同/不可比"的错误结论 + 用户一句"那为什么不照着官方，你要自己胡来"。

## 三类容易踩的 trap

| trap | 典型反例 | 正确做法 |
|---|---|---|
| 简化 API | 用 `model.generate()` 替代 `model.generate_image()` | 找官方 demo 用的是哪个，照搬 |
| 替换参数 | `bot_task="auto"` 替代 `bot_task="think_recaption"` 因为前者"看上去等价" | 看官方 demo 里 `bot_task=` 给的是什么，照搬 |
| 删掉看似多余的设置 | `model.generate_image()` 内部传了一堆 `stage_transitions` 觉得很复杂，自己跳过这步 | 这些"复杂"的设置往往就是模型的真实解码逻辑，不能省 |

## 跟 CLAUDE.md 第 9 条的关系

CLAUDE.md 第 9 条："接入新模型/新组件前，必须先做环境侦察，禁止直接写代码"——本规则是它的特例：**对齐测试也属于"接入新组件"**，必须先看官方推荐的调用方式。

历史违反次数：2026-04-21（tokenizer 没看 config 直接写代码）+ 2026-04-30（baseline 没看 README 直接写测试），都吃了亏。
