# Painterly bug — silent correctness bugs

painterly fix 期间踩到的两个"代码不崩、视觉看起来 OK，但实际是错的"silent correctness bug：dict key 静默 fallback、VAE encode 漏传 generator。共性是**我的工具栈正好不监测被 silent 掩盖的字段**。根因和总览见 [`painterly_root_cause.md`](painterly_root_cause.md)。

---

## 2026-05-06 06:00 — `user_prompt` vs `prompt` 离线 bug 我跑了 5 次都没踩到，被同事一句话点出

**症状**：cr/pr3107-fix 的 `prompt_dict = {"prompt_token_ids": ..., "user_prompt": p, ...}`，我跑 IT2I 5 次（baseline / ablate1/2/3 / cuDNN_L1 / moe_fp32）全部成功出图，painterly 修复验证通过。同事跑离线推理时报"有问题"，要求改 `"user_prompt"` → `"prompt"`。

**根因**：DiT pipeline `pipeline_hunyuan_image3.py:1294` 只读 `p.get("prompt") or ""`，**完全不识别 `user_prompt` key**。我传 `user_prompt`，DiT 拿到的 `prompt = [""]` 空字符串。

为什么我没踩到这个 bug：
1. **silent fallback `or ""`**：`p.get("prompt") or ""` 在 key missing 时返回空字符串而不是抛异常 → 代码不崩
2. **IT2I 实际生成走 `prompt_token_ids` → AR → DiT cross-attn 路径**，不依赖 `prompt` 字符串 → 视觉输出正确
3. **我只测了 img2img 一种模式**，t2t / t2i_recaption 等**主要靠 `prompt` 字符串**的模式没碰，那些模式空字符串就 garbage 了
4. **我的工具栈是"看图"**，silent fallback 让代码不崩、图不受影响 → 我的工具栈不报警

**同事怎么发现的（推测）**：直接 grep `pipeline.*\.get\(` 看 DiT 实际读哪些 key，一眼看出 `user_prompt` 不在白名单。或者跑了 t2t 模式看到空 prompt。**这是"看消费侧"的路径，比"看生成侧 + 看输出"信息密度高得多**。

**对未来的提醒**（已加到 CLAUDE.md B15 + style_bias_debug_methodology.md）：
- 给 dict-shape API 传字段前必须 grep 消费侧 `dict.get(...)`：消费侧 key 白名单 = 上游可传的 key 清单
- `dict.get("key") or fallback` 模式是 silent fallback 的典型陷阱，wrong key → empty fallback → 不崩 → silent correctness bug
- 视觉/数值"输出 OK" ≠ 代码正确：你的工具栈可能正好不监测被 silent 掩盖的字段

---

## 2026-05-07 — HunyuanImage3 AR 带图 greedy 输出每次跑不一致

**症状**：同事反馈 vllm-omni HunyuanImage3 AR 在 greedy（temperature=0）下输出 token 序列不稳定，多次跑同一 prompt+图片得到不同结果；HF 官方实现同条件下稳定可复现。

**根因**：`vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1719` 调用 `vae_encode_result.latent_dist.sample()` 没传 `generator` 参数；`autoencoder_kl_3d.py:46-54` 的 `DiagonalGaussianDistribution.sample()` 在 `generator=None` 时走全局 RNG（`x = mean + std * randn_tensor(generator=None)`）。每次 prefill VAE latent 都重新抽样 → 图像 token embedding 漂 → 进 transformer 后 logits 微动 → greedy argmax 在边界 token 翻位。HF 对应位置在 `modeling_hunyuan_image_3.py:2437` 是 `latent_dist.sample(generator)`，generator 由 `prepare_seed`（line 2362）+ `torch.Generator(device).manual_seed(seed)`（line 2775-2776）构造，所以给定 seed 时确定。**只在带图 AR（I2T/IT2I）路径触发；纯 T2T 不走 vae_encode 不受影响。**

**附带的二级 bug**：`vllm_omni/model_executor/stage_configs/hunyuan_image3_moe.yaml:28` 写 `engine_output_type: latent`，但同 yaml line 41 `is_comprehension: true` + line 43 `final_output_type: text`。模型代码 `hunyuan_image3.py:1515-1516` 只看 `engine_output_type` 决定 `_is_comprehension`，所以 `engine_output_type=latent` → `_is_comprehension=False` → 走 generation 分支启用 stage_transitions / ratio restriction，跟 yaml 表达的"comprehension/text"意图相反。`hunyuan_image3_t2i_2gpu.yaml` 同款冲突。这条不直接造成 greedy 漂，但会让 sampler 上错误的 logits processor，跟 HF think-mode 行为对不齐。

**解法**：
1. `_vae_encode` 接受 request seed，内部构造 `torch.Generator(device).manual_seed(seed)` 传给 `latent_dist.sample(generator)`。或者用 `DiagonalGaussianDistribution(deterministic=True)` 取 mean 作 latent（需先验证画质影响）
2. `hunyuan_image3_moe.yaml` / `hunyuan_image3_t2i_2gpu.yaml` 的 `engine_output_type` 改回 `text`，或确认这个 stage 是否真的应该走 generation 分支

**对未来的提醒**：
- "对齐 HF" / "greedy 不一致" 类问题第一步是 `grep -E "randn|\.sample\(|torch\.Generator|manual_seed|dropout"` 全量审计显式随机源，不要直奔 MoE/attention 嫌疑链——具体方法论见 `memory/feedback/alignment_debug.md` §1
- 让用户复现时记录"第一个分歧 token 之前的 prefix 长度"。分歧出现在图像 token 紧后第一个文本 token = VAE/multimodal embedding；分歧在几十 token 之后才出现 = TP allreduce 顺序 / bf16 atomic 这类二阶因素
- yaml 里 `engine_output_type` / `is_comprehension` / `final_output_type` 三个字段一旦冲突，优先信代码里实际读哪个——这里只读 `engine_output_type`，剩下两个是给 pipeline_registry 用的元数据，不进模型分支判断
