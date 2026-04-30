---
name: async_chunk default True breaks single-stage diffusion pipelines
description: DeployConfig.async_chunk 默认 True，单阶段 diffusion 模型没有 deploy YAML 时必须显式关闭
type: feedback
---

单阶段 diffusion 模型（如 HunyuanImage3 DIT_ONLY）启动时必须加 `--no-async-chunk`，或创建 deploy YAML。

**Why:** `DeployConfig.async_chunk` 默认 `True`。没有 deploy YAML 时用默认值。单阶段 pipeline 没有 next-stage processor，`async_chunk=True` 直接报 `ValueError`。

**How to apply:** 
- 永久修法：创建 `vllm_omni/deploy/<model_type>.yaml`，写 `async_chunk: false`
- 临时修法：启动命令加 `--no-async-chunk`
- 判断依据：单阶段 pipeline（只有 DiT，没有 AR→DiT bridge）= 必须 `async_chunk: false`
