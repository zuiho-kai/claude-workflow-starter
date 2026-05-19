# Painterly bug — conditioning 路径排除链

painterly 调查中**证明 painterly 不在 conditioning 路径上**的三步链：rebase main → 全链路数值审计 → cond_vae/cond_vit 双消融。这一系列实验都"没修"painterly，但**排除了一大片嫌疑**。根因和总览见 [`painterly_root_cause.md`](painterly_root_cause.md)。

---

## 2026-05-05 17:30 — Rebase cr/pr3107-fix → vllm-omni main (45 commits) 不修 painterly

**实验**：cr/pr3107-fix 落后 vllm-omni `origin/main` 45 个 commit，rebase 到最新 main（包括 #3285 timestep_embedding 共享重构 / #3082 Remove Entrypoint Hijack for vLLM 0.20.0 / #3327 #3302 #3307 FA backend 修复 / #3304 Z-Image RMSNorm / #3325 NPU 0.20.0 align 等），4-GPU IT2I 同 prompt + seed=42 重跑。

**结论**：painterly 视觉**完全保留**，跟 baseline 不可区分。

**对未来的提醒**：painterly 已确认**不在 vllm-omni 这 45 个 main commit 范围内**。下次别再花时间 `git log origin/main..HEAD` 找精度修复 commit。bug 必然在：(a) cr/pr3107-fix 自己的 21 个适配 commit，(b) vllm 0.20.0 / torch 2.11 / cuDNN 13 这些非 vllm-omni 组件，(c) 或 vllm-omni AR/DiT 跨进程架构本身。Branch 已 push 到 `TaffyOfficial/vllm-omni:cr/pr3107-rebased` 备查。

---

## 2026-05-05 17:45 — VAE encode + instantiate_vae_image_tokens + UNetDown 全链路数值审计 → 数值层完全清白

**实验**：BUG-PROBE env-gate dump 三个关键点的统计：
- `vae_encode` 入参 image / 出参 latent
- `instantiate_vae_image_tokens` 入口 images / 出口 scattered hidden_states
- `patch_embed` (UNetDown) 输出 image_seq

跑 IT2I 收 dump，同时静态字节级 diff vllm-omni vs HF (`modeling_hunyuan_image_3.py`) 的相关方法。

**关键数据**（cond image 真实输入路径）：
- `vae_encode` 入参 (1,3,1,1024,1024) FP32 min=-1 max=1 mean=0.408 std=0.443 ✓ 标准 VAE 输入
- `vae_encode` 出参 (1,32,64,64) FP32 mean=-0.4114 std=1.0065 ✓ 标准 VAE latent
- `instantiate_vae_image_tokens` 入口 images mean=-0.4114 std=1.0065 ← **逐位匹配 vae_encode 输出**
- `patch_embed` 输出 image_seq (2,4096,4096) BF16 std=0.1031 ✓ 合理 patchified embedding
- scatter 后 hidden_states 演化：std 从 0.0157 → 0.0736 → 0.1001（gen + cond + vit 依次注入）✓ 无溢出

**字节级 diff**（vllm-omni vs HF snapshot）：
- `vae_encode`：唯一差异是 vllm-omni `latent_dist.sample()` 没传 generator，HF 传了。autocast `dtype=torch.float16` 等价（HF config `vae_autocast_dtype: float16` 验证）
- `instantiate_vae_image_tokens`：标准路径几乎一致（HF 多一个 `if hidden_states is None` 分支用于 KV-reuse 优化模式，vllm-omni 第一步路径不走它）
- `UNetDown` (patch_embed class)：完全等价，仅格式差异

**结论**：painterly **不在 cond_vae conditioning 链路的任何数值层**。VAE encode→装配→patch_embed 全部健康。

**对未来的提醒**：
- 别再继续 dump cond_vae 链路上的数值统计——已是死胡同
- HF `vae_encode` 在 `modeling_hunyuan_image_3.py` 不在 `hunyuan_image_3_pipeline.py`，grep 别只搜 pipeline 文件
- `vae_autocast_dtype` 是 HF model config 字段（值 `float16`），vllm-omni 硬编码 `torch.float16` 等价

---

## 2026-05-05 18:00 — Cond_vae / cond_vit 双消融 → painterly 与 conditioning 路径完全无关

**实验**：env-gate `HI3_DISABLE_COND_VAE=1` / `HI3_DISABLE_COND_VIT=1` 跳过 `forward_call` 里对应 `instantiate_*_tokens` 调用。三轮 IT2I：
1. **ablate1**（关 cond_vae 留 cond_vit）：painterly 仍在；矩形从锐利平面 → 模糊 3D 立方体（cond_vae 主导精确空间布局）
2. **ablate2**（关 cond_vit 留 cond_vae）：painterly 仍在；矩形布局跟 baseline 几乎一致
3. **ablate3**（双关）：painterly **更猛**（毛茸茸 + 紫砖墙 + 油画感更强），矩形完全消失，但 painterly 风格反而更纯粹

**用户补充**：之前会话验证过"把 HF AR 输出注入 omni T2I 路径，painterly 也在"——AR latent token 也不是 painterly 来源。

**结论**：painterly **完全独立于所有 conditioning 通路**（cond_vae / cond_vit / AR latent token / cond cot text）。painterly bias 写在 **DiT body 内部 forward** 或 **vllm 0.20 / torch 2.11 / cuDNN 13 共性回归**，不在 vllm-omni 自己的装配代码里。

**剩余嫌疑面**（按可能性）：
1. `vllm.model_executor` 共享 op (RMSNorm batch-invariant rewrite / Attention layer batch-invariant dispatch / SDPA 后端选择) 在 PyTorch 2.11 + cuDNN 13 下数值漂移
2. DiT transformer body 内部 cross-attn / MoE forward
3. final_layer (UNetUp) 把 hidden_states 转 noise prediction 时偏

**对未来的提醒**：
- ablation 实验比 dump 数值更直接定位「风格 bias」类 bug（数值统计看不出方向性偏移）
- 别再继续在 cond_vae / cond_vit 上做实验——已彻底排除
- 下一步该 dump 的是 DiT body 入口/出口 hidden_states + final_layer 输入/输出，或者直接做 vllm-omni vs vllm 0.19 + torch 2.10 的精度回归 bisect
