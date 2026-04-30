# Error Book: HunyuanImage3 baseline 测试方式踩坑

## 2026-04-30 — 没看官方 README 就自造 baseline 测试方式

**症状**：
- 要测 omni `is_comprehension=false` 的 think+recaption 输出，跟 HF 对比
- 自己写脚本用 `model.generate(bot_task="auto", eos_token_id=[</recaption>, <answer>, <boi>, EOS])`，跑出 346 chars 输出
- 跟 omni 的 811 chars (think 482 + recap 329) 完全对不上
- 错误结论："两边设计不同，不可比"

**根因**：
- **没先 grep README 找官方 demo**，直接拍脑袋用 `model.generate()` + 自己设的 stop tokens
- 官方实际用 `model.generate_image(bot_task="think_recaption")`，**不是** `model.generate()`
- `generate_image()` 内部 (`modeling_hunyuan_image_3.py:3237-3320`) 拼了 `stage_transitions=[(end_of_think_id, [recap_id])]` + `final_stop_tokens=[end_of_recap_id]` 喂给 `model.generate()`
- HF 自定义的 `generate(stage_transitions=..., final_stop_tokens=...)` 跟 omni `_StageTransitionLogitsProcessor` 是同一个机制
- 直接用 `bot_task="auto"` 完全绕过 stage_transitions → HF 模型自由生成 → 拿到的不是"官方推荐跑法的输出"

**烧的成本**：
- 30+ 分钟跑 HF baseline 的失败尝试（OOM、timeout、`max_new_tokens` 重复传报错）
- 跟用户解释错误结论"think+recap 在 HF 没有可比 baseline"
- 用户一句"那为什么不照着官方，你要自己胡来"

**解法**：
重写脚本严格复刻 `generate_image()` AR 部分：
```python
# 关键参数（不能省）
stage_transitions = [(tkw.end_of_think_token_id, [tkw.convert_tokens_to_ids(tkw.recaption_token)])]
final_stop_tokens = [tkw.end_of_recaption_token_id]
model_inputs = model.prepare_model_inputs(..., bot_task="think")  # 注意 first_bot_task="think"
outputs = model.generate(
    **model_inputs, mode="gen_text", decode_text=True,
    do_sample=False, temperature=0.0,
    max_new_tokens=2048,
    stage_transitions=stage_transitions,        # ← omni 同款
    final_stop_tokens=final_stop_tokens,        # ← 在 </recaption> 停
)
```

**对未来的提醒**：
1. 接 HF 模型做对齐测试 → **第一步是 `grep -E "demo|generate_image|prepare_model_inputs" README.md`**
2. 看官方 demo 用的是 `model.generate()` 还是 `model.generate_image()` / `model.chat()` —— 照搬，不要替换成"看似等价"的简单 API
3. 看官方传的 `bot_task` / `mode` / `use_system_prompt` 取值 —— 照搬，不要拍脑袋设
4. 自定义 generate 函数（如 `generate_image`）内部拼的 `stage_transitions` / `logits_processor` 看似复杂，但这是模型真实解码逻辑——不能省
5. 详见 `memory/feedback_check_official_demo_first.md`

---

## 同期教训：HF transformers `generate()` 参数冲突

跑 HF `prepare_model_inputs(...)` 返回的 kw dict 自带：
- `max_new_tokens`（来自 generation_config）
- `eos_token_id`（来自 generation_config）

调 `model.generate(**kw, max_new_tokens=2048, eos_token_id=[...])` 会撞 `TypeError: got multiple values for keyword argument`。

**修法**：generate 前先 `kw.pop("max_new_tokens", None); kw.pop("eos_token_id", None)`，再传新值。

**对未来的提醒**：HF `prepare_model_inputs` 返回的 dict 包含完整 generation 参数，覆盖前必先 pop。这个不是 HunyuanImage3 特有，所有用 prepare_model_inputs 的 HF 模型都一样。
