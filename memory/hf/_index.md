# Memory · hf/

**何时来翻**：跑 HuggingFace 官方 baseline 对齐 vllm-omni、写 prompt 模板。HunyuanImage3 baseline 之前**必读** `hf_baseline_runbook.md` + `hf_omni_alignment_method.md`。

| 文件 | 一句话 |
|------|--------|
| [hf_baseline_runbook.md](hf_baseline_runbook.md) | HF 官方 baseline 完整运行手册：必修 bug fix、profiler 精确控制、参数陷阱、完整脚本 |
| [hf_omni_alignment_method.md](hf_omni_alignment_method.md) | vllm-omni ↔ HF 离线推理对齐 5 步方法论（FA/SDPA → prompt → input_ids → prompt_token_ids → image embedding/BF16） |
| [official_prompt_format.md](official_prompt_format.md) | 官方 HF Instruct 模板（T2T/I2T/IT2I 通用）、BPE 边界陷阱、image `<timestep>` 展开差异 |

> HF cache 环境变量陷阱（`TRANSFORMERS_CACHE` / `HF_HUB_CACHE`）见 [`remote/hf_cache_env_gotcha.md`](../remote/hf_cache_env_gotcha.md)。
