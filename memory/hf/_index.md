# Memory · hf/

**何时来翻**：跑 HuggingFace 官方 baseline 对齐 vllm-omni、写 prompt 模板。HunyuanImage3 baseline 之前**必读** `hf_baseline_runbook.md` + `hf_omni_alignment_method.md`。

| 文件 | 一句话 |
|------|--------|
| [hf_baseline_runbook.md](hf_baseline_runbook.md) | HF 官方 baseline 完整运行手册：必修 bug fix、profiler 精确控制、参数陷阱、完整脚本 |
| [hf_omni_alignment_method.md](hf_omni_alignment_method.md) | vllm-omni ↔ HF 离线推理对齐 5 步方法论（FA/SDPA → prompt → input_ids → prompt_token_ids → image embedding/BF16） |
| [official_prompt_format.md](official_prompt_format.md) | 官方 HF Instruct 模板（T2T/I2T/IT2I 通用）、BPE 边界陷阱、image `<timestep>` 展开差异 |
| [run_image_gen_demo_runbook.md](run_image_gen_demo_runbook.md) | 跑官方 GitHub demo `run_image_gen.py`：隐式 deps、flashinfer 首跑 7min JIT 假死、device_map=auto 不支持 TP、time budget |
| [hf_alignment_pitfalls.md](hf_alignment_pitfalls.md) | 接 trust_remote_code 模型踩坑合集：必先 grep 官方 demo 找入口、读 requirements.txt 别猜版本、改 snapshot 不改 modules cache、有 runbook 直接照抄 |

> HF cache 环境变量陷阱（`TRANSFORMERS_CACHE` / `HF_HUB_CACHE`）现在合并在 [`../remote/container_setup.md`](../remote/container_setup.md)。
