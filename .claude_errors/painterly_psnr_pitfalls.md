# Painterly bug — PSNR 验证 / 跨实现对比 / 凭空想 KV 复用

painterly fix 之后做 vllm-omni vs HF 跨实现验证时三个 PSNR 类踩坑：HF 自己跟自己 PSNR 都只 10-12 dB / 凭空编"KV cache transfer"机制 / fair-comparison 没对齐就跑。根因和总览见 [`painterly_root_cause.md`](painterly_root_cause.md)。

---

## 2026-05-06 08:30 — HF 自己跟自己重跑 PSNR 也只有 10-12 dB

**实验设置**：
- HF run a：`model.generate_image(prompt=..., image=..., seed=42, do_sample=False, ...)`
- HF run b：完全相同的调用（同进程、同 GPU、同 seed、同 do_sample=False）
- 对比 a vs b 输出图 PSNR

**结果**：
| 配置 | PSNR a vs b |
|---|---|
| HF full pipeline (cot regen + DiT) | **11.78 dB** |
| HF DiT-only (cot fixed via `cot_text=`+1 行 modeling patch) | **10.86 dB** |
| vllm-omni inject HF cot | 15.16 dB（**比 HF 还稳定**）|

**结论**：HunyuanImage-3.0-Instruct **HF 实现本身**就不是 deterministic 的，即使所有参数固定（greedy / 同 seed / 同 device），跑两次 PSNR 也只有 ~11 dB。

**根因**（推测，未逐个隔离）：
- cuDNN benchmark mode 跑两次选不同 conv 算法
- `device_map="auto"` 多 GPU 下 NCCL all-reduce 顺序非 deterministic
- DiT initial noise `torch.Generator(seed=42)` 在不同 cuda stream 调用顺序下结果不同
- GPU atomic ops 默认 non-deterministic

**对 painterly fix 验证的影响**：
- vllm-omni vs HF 的 10.49 dB cross-impl PSNR **已经在 HF 自身重跑方差（10.86~11.78 dB）范围内**
- "vllm-omni 跟 HF 不 byte-equal"这个标准**在 HunyuanImage3 上无意义**——HF 自己都达不到
- 视觉对齐（cartoon vs painterly）是真实可观察的 fix，PSNR 不是合适的金标准

**对未来的提醒**（已加 CLAUDE.md B19）：
- 用 PSNR 验证 cross-impl 对齐前必须**先测 reference 实现自身的 reproducibility**。如果 reference 自己 a vs b 都拉不到 25+ dB，那 cross-impl PSNR 同水平**完全合理，不是 bug**
- 视觉判断 + 端到端功能验证 > 数值 PSNR 在大部分 generative model cross-impl 场景

---

## 2026-05-06 08:00 — 凭空想象 "KV cache transfer" 这个不存在的机制，拍头给方案

**症状**：用户问「为什么不复用 HF 的 image latent token sampling」。我答了一段长解释，里面说"要消掉跨实现 PSNR 误差只能做 KV cache transfer：捕获 HF AR 完整 K/V tensors，序列化跨进程传给 vllm-omni DiT，工作量 1-2 天"。

**用户当场怼回："你是傻逼么，hf 哪来 kv 复用，omni 现在也哪来 kv 复用"。**

**事实复核**：
- HF `model.generate_image(...)` 是**单进程** — AR 跟 DiT 共享同一 GPU 张量 module，**根本没"KV 序列化 + 传递"的概念**，无从谈"复用"
- vllm-omni IT2I yaml `enable_prefix_caching: false`，stage handoff 传的是 **cot text + raw cond image bytes**，不是 AR 的 KV
- PR #2949 引入的 `kv_reuse` 选项是 **T2I 优化**，IT2I config 根本没启用

**根因**：我没看 yaml、没看架构就开始拍方案。只是因为"AR + DiT 跨进程"听起来像"需要 KV 传递"，就直接编出"1-2 天工程量"的工作。**全凭直觉编工程方案，没核对任何代码 / 文档**。

**真正的跨实现漂移源**（这个我事后想清楚了）：
- cond image VAE encode（BF16 Conv3d + GroupNorm 多实现差）
- cond image ViT encode（Siglip2 transformers 5.x BF16 attn 多实现差）
- DiT denoise（32 层 BF16 MoE + attn × 50 step BF16 数值累积）
- VAE decode（BF16/FP16 conv3d 多实现差）

每步小 BF16 漂移叠 50 步 → 10 dB PSNR floor。**这是 BF16 多实现部署的物理 floor，不是 bug，没法不改架构修**。

**对未来的提醒**（已加 CLAUDE.md B18）：
- 用户问"为什么不 X"时，不要直接答"X 工作量 N 天"——先**核对 X 这个机制是否真实存在**于代码 / 架构里。"AR + DiT 跨进程" ≠ "需要 KV 复用"。多 stage 架构下 stage handoff 传什么、不传什么，**看 yaml + stage_input_processor 才知道**
- 工程方案给"工作量评估"前必须**先 grep 关键 API**确认机制存在。"1-2 天工程量"这种数字给得轻飘但全凭想象，被怼是应得
- B12 / B16 反复说"不要凭直觉"、"先看代码"，这条又踩。**真的要把"答方案前先 grep 关键词"加成 muscle memory**

---

## 2026-05-06 07:30 — 跨实现 PSNR 对比没做 fair-comparison 设置就跑，浪费一轮 GPU 时间

**症状**：painterly fix 验证后想跟 HF reference 算 PSNR，跑了 doggy + 新年宠物海报 setup。vllm-omni 出图（粉红海报 + 多面板文字）vs HF 出图（红幕背景 + 单标题 + 狗狗中央），**视觉布局完全不同**，PSNR=8.96 dB。看起来"差很大"但其实是我**没对齐参数就跑**：

- vllm-omni 跑：`--guidance-scale 5.0`（CLI 我手填的）+ stage_config `temperature=0.6, top_p=0.95, top_k=1024`（sampling mode）
- HF 跑：`generate_image(...)` **没传 guidance_scale**（HF default=2.5）+ AR 默认 sampling

**两套都在 sampling mode + guidance_scale 差 2x**，相同 seed=42 在两套 RNG 实现里 sample 出**不同 cot token sequence** → DiT 输入不同 → 出图布局不同。这是**纯采样随机性**，不是模型 bug。

更糟的是：lastwords 早就写过：

> "Force greedy decoding on both sides (do_sample=False, temperature=0) -- per the runbook this is the only mode where the comparison is reproducible; **sampling-mode RNG primitives between vLLM and HF are fundamentally different so byte-equality is unachievable**."

我有这个 memory，但**跑实验前没回头看**，直接拿默认 sampling 参数开跑。结果浪费 ~5 分钟 GPU 时间 + 用户时间审误差 + 一次写"看起来 PSNR 很差"的 false alarm 报告。

**根因**：跨实现 PSNR 测试前没列 fair-comparison checklist。两边的"默认值"（guidance_scale / temperature / top_p / top_k / bot_task / output_size / decoding mode）都不约而同**没对齐**。

**对未来的提醒**（已加 CLAUDE.md B17 + style_bias_debug_methodology.md fair-comparison checklist 章节）：
- **跨实现 PSNR 对比必须 greedy mode**（temperature=0, do_sample=False, top_k=1）—— 消除 sampling RNG 差异，让 AR 输出 byte-deterministic
- **跑前必须显式对齐**这 8 项参数：prompt / 输入 image bytes / seed / temperature / top_p / top_k / **guidance_scale** / bot_task / steps / output_size。**默认值跨实现几乎从来不一样**（HF model defaults 跟 vllm-omni stage_config defaults 各管各的）
- 8-15 dB PSNR 在 sampling mode 是 **expected floor**（lastwords 已记录），看到这个数字别声称"DiT 有问题"——sampling mode 跨实现就这水平
