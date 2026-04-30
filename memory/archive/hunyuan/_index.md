# Memory · archive/hunyuan/

**何时来翻**：只在重新接触 HunyuanImage-3.0-Instruct 接入工作时回看。这些是项目结束后的"考古资料"——alignment 盘点、MoE router fp32 对齐、AR↔DiT 桥接、双向注意力、profiling 基线、stage device race、CI 进度等模型强绑定细节。日常开发不需要读。

| 文件 | 一句话 |
|------|--------|
| [hunyuan_image3_alignment_inventory.md](hunyuan_image3_alignment_inventory.md) | PR #3243 最终态完整盘点：10 commits / 4 files、image embedding 6 层、Mode 1+2 对齐数据 |
| [hunyuan_image3_moe_fp32_router.md](hunyuan_image3_moe_fp32_router.md) | MoE router fp32 对齐 HF：`custom_routing_function` 绕过 bf16 topk_softmax + static_forward_context / OOM trap |
| [ar_dit_bridge.md](ar_dit_bridge.md) | AR→DiT 数据桥接：HunyuanImage3 必须传 `cot_text` 字符串而非 raw token IDs |
| [bidirectional_attention.md](bidirectional_attention.md) | 图像 token 双向注意力：把 `hunyuan_image_3_moe` 加进 vllm 上游 `MM_PREFIX_LM_MODELS` |
| [stage_device_mapping_race.md](stage_device_mapping_race.md) | DP 多引擎并发 `CUDA_VISIBLE_DEVICES` 竞态根因（PR #3207 + ca5e329b） |
| [profiling_tp4_fp8_baseline.md](profiling_tp4_fp8_baseline.md) | tp4_fp8 基线：2.85s 延迟 / 1.15s `model.forward` |
