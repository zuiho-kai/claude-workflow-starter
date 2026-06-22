# Painterly bug — 调查总览 + 根因（连同事后更正）

HunyuanImage3 IT2I "扁平卡通输入 → 油画风输出" painterly drift 的核心调查链：5h 错路径 + 30min 在 hint 后定位 + 事后被同事二次更正。具体调查方法上的踩坑见 [`painterly_debug_methodology_misses.md`](painterly_debug_methodology_misses.md)，conditioning 路径排除链见 [`painterly_conditioning_ablation.md`](painterly_conditioning_ablation.md)，本 PR 派生的踩坑见 [`painterly_plan_size_misjudge.md`](painterly_plan_size_misjudge.md)、[`painterly_psnr_pitfalls.md`](painterly_psnr_pitfalls.md)、[`painterly_silent_bugs.md`](painterly_silent_bugs.md)。

---

## 2026-05-06 02:50 — 🎯 ROOT CAUSE FOUND: BF16 vs FP32 gate routing in DiT MoE

**Painterly bug 根因（实锤）**：vllm-omni 的 **diffusion-side** `HunYuanSparseMoeBlock` (`vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py:1455+`) 创建 `self.gate = ReplicatedLinear(...)` 时**没指定 `params_dtype=torch.float32`**，默认走 BF16。HF reference (`modeling_hunyuan_image_3.py`) 严格用 FP32 gate routing。DiT 32 层 × top-k=8（256 expert 选 top-8），BF16 routing 在 logits 接近时**翻牌**，逐层累积 → painterly bias attractor。

**讽刺的是**：vllm-omni 仓库**已经有正确实现** —— `model_executor/models/hunyuan_image3/hunyuan_image3.py:HunyuanImage3SparseMoeBlock`（这是 HF AR 模型用的）。它继承 `HunYuanSparseMoeBlock` 且修了 routing：
- `params_dtype=torch.float32` for `self.gate`
- 显式 `hidden_states.float()` cast 后跑 gate
- FP32 `softmax` + `topk` + `clamp(min=1e-8) + divide` renormalize
- pack `(topk_weights, topk_indices)` 喂 `SharedFusedMoE` 的 `custom_routing_function=_hunyuan_image3_unpack_packed_topk`，绕开 vllm 的 BF16 `topk_softmax` CUDA op

但 **diffusion-side 漏了同步这套修复**。一年前的事实：HunyuanImage3 训练时就要求 FP32 routing（它在 HF `hunyuan_image_3_pipeline.py` 里就写了 `with torch.autocast('cuda', enabled=False)` 包 routing）。AR 那边修了（model_executor 版），DiT 这边遗漏。

**修复 patch**（4 处改动 in `hunyuan_image3_transformer.py:HunYuanSparseMoeBlock`）：
1. **line 1486-1492**：`self.gate = ReplicatedLinear(..., params_dtype=torch.float32, quant_config=None, ...)`
2. **line 1483-1485**：加 `self.top_k = top_k`（forward 需要）
3. **line 1514-1527**：`HunyuanFusedMoE(...)` → `SharedFusedMoE(..., custom_routing_function=_hunyuan_image3_unpack_packed_topk, pcp_size=1)`（注意 `pcp_size=1` 不能删，否则触发 `prefill context parallel group is not initialized` AssertionError）
4. **line 1529-1545 forward**：FP32 routing pipeline — `self.gate(hidden_states.float())` → softmax (fp32) → topk → clamp+divide → cast topk_weights to bf16 → cat[topk_weights.float(), topk_indices.float()] → 喂给 `self.experts` 作为 `router_logits`

**视觉验证**（cr/pr3107-fix on /rebase/vllm-omni/, vllm 0.20.0 + torch 2.11.0+cu130）：
- baseline (BF16 routing): painterly 毛茸茸猫 + 水彩矩形 + 纸纹背景
- patch 后: clean cartoon 平涂橙猫 + 锐利彩色矩形 + 干净浅蓝背景，跟 HF reference `output_hf_dit.png` 风格一致

**为什么这能解释一整轮调研所有现象**：
- ✅ painterly 不在 cond_vae / cond_vit / VAE encode / 装配 / patch_embed 数值层 —— routing bias 是 **layer-wise，影响所有 token，跟 conditioning 无关**
- ✅ 注入 HF AR cot 不修 —— DiT 内部 routing 还是 BF16
- ✅ rebase vllm-omni main 不修 —— main 没改 diffusion-side moe
- ✅ ablate1/2/3 全 painterly —— routing bias 持续存在
- ✅ TF32 关掉无效 —— 不是 kernel-level，是 dtype 选择问题
- ✅ HF reference 跑 cartoon —— HF 用 FP32 gate
- ✅ QwenImage 同样问题（colleague 报告）—— 大概率同类 bug：MoE gate dtype 没对齐 HF

**对未来的提醒**：
- 接入 MoE 模型走 vllm 0.20+ 时，`gate` 的 `params_dtype` **必须**显式指定（不要靠默认）。HunyuanImage3、Qwen3-MoE、DeepSeek-V2 等所有"训练时 FP32 routing"的模型都要这么搞
- 当一个仓库**同时有 AR 版和 DiT 版**模型代码（model_executor/ vs diffusion/），**两边的 MoE 实现必须保持同步**。AR 那边修过的 bug（如 FP32 routing）DiT 这边大概率也有
- 调试**风格漂移类 bug**（painterly / sketch / oil）时，**MoE routing 是首选嫌疑** —— 因为风格 bias 跟"逐层 expert 选择微偏 → DNN 聚合到不同 attractor"对得上。逐 op 数值统计 dump 看不出来（每层 std/mean 健康，但 expert 选择已偏）

---

## 2026-05-06 03:30 — 🪞 META REFLECTION: 5h 走错工具栈，同事一个 hint 30 分钟定位

**症状**：painterly bug 实际定位用了**两条路径**：
- 错的（5h）：rebase + 数值 dump probe（VAE encode / instantiate / patch_embed）+ cond ablation × 3 + cuDNN/TF32 stability flag → 全部不修
- 对的（30min after hint "FusedMoE"）：单 Explore agent 静态 diff vllm-omni `diffusion` 版 vs `model_executor` 版 MoE → 当场发现 BF16 vs FP32 gate routing 差异

**根因（meta level）**：把"风格 bias"类 bug 当"数值幅度漂移"类 bug 处理。两者用完全不同工具栈：

| 类型 | 表现 | 工具 |
|---|---|---|
| 数值幅度漂移 | inf/nan、saturation、值爆炸 | dump mean/std/min/max |
| **方向性 bias**（painterly/blur/style shift）| 每层数值都健康，但 expert dispatch 决策每层偏一点累积 | **代码 diff vs HF reference**，dump 看不出来 |

painterly 的指纹不在 hidden_states 统计里，写在 expert routing histogram 里 —— 我从头到尾没看过那个。我打的 6 个 BUG-PROBE 全是"找数值不健康的迹象"，但 BF16 routing 漂移恰好不会让数值不健康。

**为什么 anchor 错**：
1. 沿用 prior session "qwenimage 也有 → cuDNN/PyTorch/vllm 0.20 共享 infra 回归"的框架。**这个框架可能只是"两个团队都漏了同款 fix"**，不必然指向共享 infra。
2. 视觉症状 "rectangle painterly + prompt 改不了" → 推 cond image 通路 bug → 沉到 conditioning 链路。但 conditioning 跟 MoE routing 是不同 op layer，逻辑上 routing bias 也能产生这种症状（layer-wise 影响所有 token）。
3. lastwords 写 "MoE routing 已证伪" → 我视而不见地信任。**那只证伪了一个具体 hypothesis**（router_logits 传错），不证明 MoE 整体清白。dtype 是 different bug。

**hint "FusedMoE" 起的作用**：打破 anchoring，从"共享 infra"切到"具体组件"，触发 diff 思维 —— **vllm-omni 自己仓库就有两个 MoE 实现**（diffusion vs model_executor），diff 它俩立刻看到 `params_dtype=torch.float32` 的差异。

**应该早做的事**：session 第一小时 grep `MoE / FusedMoE / gate` 在 vllm-omni `diffusion/` 跟 `model_executor/` 子目录里，**diff 两个实现** —— 30 分钟内 painterly bug 暴露。**这一步比所有 dump probe 都信息量大**。

---

## 2026-05-06 06:30 — 🔥 我的 FP32 routing 根因解释**也是错的**：真正的 bug 是 `process_weights_after_loading` 双调用

**事实更正**（同事 review 后指出）：painterly 的真正修复不是"FP32 routing 对齐 HF"，而是 patch 副作用 —— 把 `HunyuanFusedMoE` swap 成 `SharedFusedMoE` 时**间接删除了 `_initialize_kernel_hook` forward pre-hook**。

**真正的 bug 机制**：

`vllm_omni/diffusion/models/hunyuan_image3/hunyuan_fused_moe.py:32`:
```python
self._init_hook_handle = self.register_forward_pre_hook(self._initialize_kernel_hook, with_kwargs=True)
```
这个 hook 在第一次 forward 时跑 `self.quant_method.process_weights_after_loading(self)`。

但 vllm 0.20 standard model loader (`base_loader.py:80`) 在加载完 weights 后**已经**调过一次 `process_weights_after_loading`。vllm 内部用 `_already_called_process_weights_after_loading` flag 防双调，但**`HunyuanFusedMoE` hook 直接调 `quant_method.process_weights_after_loading(self)` 绕过了 layer-level flag** → 双调用。

`process_weights_after_loading` 不是 idempotent —— 第二次基于已 packing/quantize 过的 weight 状态再 process，破坏 weight layout / scale / 分块 → expert MLP forward 用错 weight → 32 层逐 token 累积 → painterly bias。

**为什么我的 30+ 行 patch 修了**：里面**唯一起作用**的是 class swap `HunyuanFusedMoE` → `SharedFusedMoE`（= 原 `FusedMoE`，没有 wrapper 子类的 hook） → 没有重复 hook → weight 没被双重 process → painterly 消失。

**我归因错的过程**：
- 我同时改了 5 处：(1) gate `params_dtype=fp32` (2) `quant_config=None` (3) class swap (4) `custom_routing_function` (5) external fp32 forward 重写
- 跑出来 cartoon → 我**理所当然**把功劳给了"看起来 cartoon-related 的 FP32 routing"路径
- 实际起作用的是 (3) class swap 的**副作用**（删了 hook），(1)(2)(4)(5) 都是不必要的
- model_executor 版（HunyuanImage3SparseMoeBlock）跑得对**不是因为 FP32 routing**，是因为它**没用 `HunyuanFusedMoE` wrapper**（直接用 `SharedFusedMoE`），同样避开了 hook bug

**最小修复版本**（同事确认）：
- 在 `hunyuan_fused_moe.py:32` **注释掉 / 删除** `register_forward_pre_hook(...)` 这一行
- 整个 patch 缩到 **1 行删除**

**深层教训**：
1. **多变量同时改 → 不能独立归因**。我同时改了 5 处，cartoon 出来时我把功劳给了 (1)(2)(4)(5) 那些"语义上跟 cartoon 强相关"的改动，但真正的修复是 (3) 这个看起来"只是接口切换"的改动的副作用。**应该先做最小消除实验**（每个改动单独 toggle）来归因，不能跑通就声称"找到根因"
2. **静态 diff 看代码 ≠ 看清因果**。我对比 model_executor vs diffusion 看出 FP32 routing 差异，但**没注意到** model_executor 没用 `HunyuanFusedMoE` wrapper 这个**更基本的差异**。"看到差异" 跟 "差异就是 root cause" 之间还有一步因果验证我没做
3. **"我之前那条已经写到 .claude_errors 的"meta reflection"也是错的**。我落盘"5h 错路径 + hint 后 30min 找到 FP32 routing"作为成功故事 —— 实际上 30min 找到的是**正确的代码区域**（MoE block diff），但**错误的具体机制**（FP32 routing 而不是 hook 双调用）。同事二次 review 才把机制指对。**找到正确的代码区域 ≠ 找到 root cause**

**对未来的提醒**（已加 CLAUDE.md B15 + style_bias_debug_methodology.md）：
- 多处改动一起跑通 → 必须做**最小消除实验**（一处一处 revert，看哪一处真正起作用）才能归因
- 找到代码差异不等于找到 bug 机制 —— 差异 → 假设 → **隔离实验** → 才确认机制
- "成功修复"的反思也可能是错的：成功是结果，机制要单独验证
