# HunyuanImage3 DiT Group Batch 会议讲解稿

> 行号基于当前 PR 分支 `codex/hunyuanimage3-step-batch`。这份稿子面向会议 battle：先讲清楚“为什么这样改”，再按代码块逐行解释核心改动，最后准备常见质疑的回答。

## 1. 一句话结论

这次 PR 没有绕开 `DiffusionEngine` 的 request-mode 限制，而是让 `HunyuanImage3Pipeline` 接入已有 step-wise diffusion contract。这样 DiT 每个 denoise step 都由 continuous batching scheduler 调度，同一 step、同一兼容参数的多个请求可以合成一个 DiT forward。

第一版支持的是保守的 grouped batching：

- 支持：同分辨率、同 denoise schedule、同 CFG 模式、同并行配置的多请求 DiT batch。
- 支持：不同 prompt token length，通过 right padding 做 batch collation。
- 暂不支持：异分辨率 MixFusion、sequence parallel、CFG parallel、同请求多图输出。
- 默认配置不变：deploy yaml 仍保持 `max_num_seqs: 1`，能力是 opt-in。

## 2. 整体链路

```text
AR stage / user request
        |
        v
DiffusionRequestState
        |
        v
HunyuanImage3Pipeline.prepare_encode(state)
  - tokenizer / prompt utils / condition image
  - prepare_model_inputs
  - per-request scheduler deepcopy
  - request-local AR KV / prompt KV metadata
  - latents / timesteps / CFG info
        |
        v
StepScheduler.schedule()
  - 只挑同 SamplingParamsKey 的请求
  - 只 batch 同 step_index 的请求
  - 新请求先 catch up，再进入同批
        |
        v
InputBatch.make_batch(states)
  - latents 合并
  - states 透传给 pipeline
        |
        v
HunyuanImage3Pipeline.denoise_step(input_batch)
  - merge model_inputs
  - CFG 维度展开
  - DiT forward
  - split model_kwargs 回 request state
        |
        v
HunyuanImage3Pipeline.step_scheduler(state, noise_pred)
  - request-local scheduler.step()
  - 更新 state.latents / step_index
        |
        v
post_decode(state)
  - VAE decode
  - image postprocess
```

核心点：batch 不是在 encode 阶段硬要求 prompt 一样，而是在 DiT forward 前把每个 request 已经准备好的 `model_inputs` 做 padding/merge。encode 可以逐 request 做，denoise 才组 batch。

## 3. 核心代码逐段讲解

### 3.1 Pipeline 声明支持 step execution

文件：`vllm_omni/diffusion/models/hunyuan_image3/pipeline_hunyuan_image3.py`

`315`

```python
supports_step_execution: ClassVar[bool] = True
```

逐行解释：

- 这行把 HunyuanImage3 从“只能 request-mode 一次跑完整 denoise loop”切到“可以被 step scheduler 逐步调用”。
- scheduler 看到 pipeline 支持 step execution 后，才会走 `prepare_encode -> denoise_step -> step_scheduler -> post_decode` 这套协议。
- 这不是默认打开 `max_num_seqs > 1`；是否组 batch 仍由配置里的 `step_execution`、`max_num_seqs`、sampling key 和调度器共同决定。

### 3.2 早失败：只放行当前真正支持的组合

`455-467: _ensure_step_execution_supported`

逐行解释：

- 读取当前请求的 `sampling_params`。
- 拒绝一个请求生成多张图。第一版 batch 维度定义为“请求数”，不是“每请求多图数”。
- 拒绝 custom timesteps / sigmas。原因是不同 denoise schedule 不能安全 co-batch。
- 拒绝 sequence parallel。当前合批逻辑没有实现 SP 下的序列切分和跨 rank collation。
- 拒绝 CFG parallel。当前实现让 CFG 作为 batch rows 展开，不再叠 CFG parallel。
- 错误使用 `ValueError` 明确暴露，不 silent fallback 到 `max_num_seqs=1`。

会议口径：这个 guard 是第一版的安全边界。它不是说这些永远不能支持，而是不让用户以为已经支持了。

### 3.3 从请求里抽取 prompt / AR / condition image 信息

`469-516: _extract_step_prompt_inputs`

逐行解释：

- 从 `sampling_params` 里拿 HunyuanImage3 所需的 prompt 相关字段。
- 兼容 T2I 和 IT2I：有 condition image 时走 image edit / IT2I 语义，没有时走 text-only。
- 保留 AR stage 产出的 COT 文本，使 AR->DiT 流程的 prompt 语义不丢。
- 校验同一个 DiT batch 不能混用互斥模式，比如一部分请求有 condition image，一部分没有。
- 这里不要求 prompt 字符串相同，也不要求 token length 相同；这里只负责把每个 request 的输入抽出来。

### 3.4 AR KV reuse 的 request-local 化

`518-537: _extract_ar_kv_from_sampling`

- 从 sampling params 中取 AR stage 传下来的 KV。
- 没有 KV 时返回空结构，由后续 guard 判断是否需要处理。
- 这一步只是读取，不修改 pipeline 全局状态。

`539-548: _snapshot_injected_ar_kv`

- 在 `prepare_encode` 里调用 `_maybe_handle_ar_kv_reuse` 后，pipeline layer 上会短暂挂入 AR KV。
- 这个函数把每层注入的 AR KV 拍快照，放进当前 `DiffusionRequestState.extra`。
- `clear=True` 时会清掉 pipeline layer 上的临时 KV，避免下一个 request 读到上一个 request 的 AR KV。

`550-568: _restore_injected_ar_kv`

- 在 `denoise_step` 真正 forward 前，把当前 batch 内每个 request 的 AR KV 按 batch 顺序重新拼回 layer。
- 关键是 request-local：每个 state 自己持有自己的 AR KV，不靠 pipeline 上残留的全局变量。

`570-614: _capture_prompt_kv_cache / _restore_prompt_kv_cache`

- 第一个 denoise step 后，DiT 会产生 prompt KV cache。
- `_capture_prompt_kv_cache` 把合批后的 KV 按 request 拆回各自 state。
- 后续 step 调 `_restore_prompt_kv_cache` 再按当前 batch 组合拼回去。
- 这样支持连续 batching 的动态组合：第 10 步和你同批的 request，不一定和第 1 步同批。

### 3.5 不同 prompt 长度的 padding / merge / split

`616-625: _step_sequence_pad_value`

- 给不同字段定义 padding 值。
- `input_ids`、position ids、attention mask、tokenizer outputs 的 pad 语义不同，不能一律填 0。
- 这里把 pad policy 集中起来，避免散在 merge 逻辑里。

`627-668: _right_pad_step_tensors`

- 输入是一组来自不同 request 的 tensor。
- 先找出 sequence 维度最大长度。
- 对短的 request 做 right padding。
- 对 attention mask 这类 4-D tensor，同时 pad query/key 两个方向。
- 如果不是 sequence length 差异，而是 batch 以外的真实 shape 不兼容，直接报错。
- 这就是“不同 prompt 可以组 batch”的关键：prompt token length 不同不再要求完全相等。

`670-711: _merge_batch_value`

- 递归处理 tensor、list、tuple、dict。
- tensor 走 padding 后再 `torch.cat`。
- CFG 情况下按 CFG branch-major 顺序拼 batch rows。
- branch-major 的好处是和 HunyuanImage3 既有 CFG / KV 复用布局保持一致。

`713-735: _split_batch_value`

- 是 `_merge_batch_value` 的逆操作。
- DiT forward 返回的新 `model_kwargs` 仍是合批形态，需要按 request 拆回各自 state。
- 这样下一步调度即使 batch 组合变了，也能从每个 request 自己的状态继续。

`737-772: _merge_step_model_inputs`

- 从 `input_batch.states` 取本轮参与 forward 的 request states。
- 校验所有 request 的 `cfg_factor` 一样。
- 校验所有 request 的 `step_index` 一样。
- 校验不能把 first step 和 later step 混在一个 DiT batch 里，因为 first step 要注入 AR KV，later step 要恢复 prompt KV。
- 合并每个 state.extra 里的 `model_kwargs`、`input_ids`、`attention_mask`。

`774-791: _split_step_model_inputs`

- forward 后把新的 input ids / model kwargs 拆回 state。
- 后续 step 继续用 request-local 的 `state.extra`。
- 这一步是 continuous batching 的关键：batch 只是瞬时执行形态，长期状态仍属于 request。

### 3.6 prepare_encode：把 request-mode 的准备逻辑拆成单请求状态

`1703-1821: prepare_encode`

逐行级别解释：

- 调 `_ensure_step_execution_supported`，先把不支持的组合挡住。
- 解析 sampling params，拿 prompt、system prompt、AR COT、condition image。
- 计算 height / width，默认仍按 HunyuanImage3 既有 1024 逻辑。
- 读取 `num_inference_steps`、`guidance_scale`。
- 复用既有 `prepare_model_inputs(...)`，不重写 tokenizer / prompt template / image processor。
- 对 AR->DiT 请求调用 `_maybe_handle_ar_kv_reuse`，让既有 AR KV reuse 逻辑继续生效。
- 计算 `cfg_factor = 1 + int(guidance_scale > 1.0)`。
- 调 `retrieve_timesteps(...)` 得到 request 自己的 timesteps。
- 调 `prepare_latents(... batch_size=1 ...)` 为当前 request 生成初始 latent。
- 生成 latent 使用 request-local generator / seed，避免 batch composition 改变随机数。
- 把 latent cast 到 `float32`。原因是 scheduler step 输出是 fp32；如果新加入的 request 还是 bf16，staggered batch 会遇到 dtype 不一致。
- `copy.deepcopy(self.scheduler)`，放入 `state.extra["scheduler"]`。
- 这样每个 request 有自己的 scheduler `_step_index`，不会多个 active request 共享 pipeline scheduler 的 mutable state。
- 构造 generalized causal attention mask：text causal，image span bidirectional。
- 把 `model_kwargs`、`input_ids`、`attention_mask`、`timesteps`、`scheduler`、`generator`、`cfg_factor`、`guidance_scale`、AR KV、输出尺寸等写进 `state.extra`。
- 设置 `state.latents`、`state.timesteps`、`state.step_index = 0`。

会议口径：`prepare_encode` 是“单请求 staging”，不是 batch 点。batch 点在后面的 `denoise_step`。

### 3.7 denoise_step：真正把多个请求合成一个 DiT forward

`1823-1893: denoise_step`

逐行级别解释：

- 从 `input_batch.states` 拿当前调度器选中的请求。
- 调 `_merge_step_model_inputs` 合并每个 request 的 model inputs。
- 设置 pipeline 当前 guidance scale，保持既有 CFG operator 语义。
- 根据 `step_index` 判断是 first step 还是 later step。
- first step 恢复 AR KV；later step 恢复 prompt KV cache。
- `torch.cat([input_batch.latents] * cfg_factor)` 把 CFG 维度展开到 batch rows。
- 两个请求、`guidance_scale=2.5` 时，真实 DiT row 数是 `2 requests * 2 CFG rows = 4`。
- 调 `prepare_inputs_for_generation` 复用原 pipeline 的 DiT 输入准备逻辑。
- 在 bf16 autocast 下调用 DiT forward。
- 把 noise prediction 转回 fp32，和 scheduler step dtype 对齐。
- 如果 CFG 开启，按 CFG branch chunk 后调用 `pipe.cfg_operator(...)`。
- first step forward 后调用 `_capture_prompt_kv_cache`，把合批 prompt KV 拆回 request-local state。
- 如果不是最后一步，把 forward 产出的新 `model_kwargs` 拆回每个 state，供下一 step 使用。
- 返回当前 request 顺序对应的 `noise_pred`，交给 scheduler 更新 latents。

### 3.8 step_scheduler：只更新当前 request 自己的 scheduler

`1895-1917: step_scheduler`

逐行解释：

- 从 `state.current_timestep` 拿当前 timestep。
- 从 `state.extra["scheduler"]` 拿 request-local scheduler。
- 调 `scheduler.step(noise_pred, timestep, state.latents, generator=...)`。
- 更新 `state.latents`。
- cast 到 fp32，避免下一次合批时 dtype 分裂。
- `state.step_index += 1` 推进当前 request。
- 不修改 `self.scheduler._step_index`，所以不会串请求。

### 3.9 post_decode：保持既有 VAE decode / output 语义

`1919-1955: post_decode`

逐行解释：

- 如果 output type 是 latent，直接返回 latent。
- 否则按 HunyuanImage3 既有 scale / shift 把 latent 转回 VAE 输入空间。
- 必要时补 temporal dim。
- 在 fp16 autocast 下 VAE decode。
- 调 image processor postprocess。
- 保留 AR COT 文本到 custom output，避免 AR->DiT 输出格式退化。

## 4. Generic scheduler / input batch 改动

### 4.1 SamplingParamsKey 增加 denoise schedule 维度

文件：`vllm_omni/diffusion/sched/interface.py`

`42-54`

```python
class SamplingParamsKey:
    ...
    num_inference_steps: int | None = None
```

解释：

- grouped batching 不能把 30-step 和 50-step 请求放一起。
- 加这个字段后，调度器的 compatibility key 会把不同 denoise schedule 分开。
- 这是 correctness guard，不是性能优化。

### 4.2 StepScheduler 只 batch 同 step 请求，并支持 catch up

文件：`vllm_omni/diffusion/sched/step_scheduler.py`

`67-128: schedule`

逐行级别解释：

- 先清理已经完成或 abort 的 request。
- 从 waiting queue 里挑和当前 active group 兼容的请求。
- 如果没有 active request，新请求可以直接 admitted。
- 如果已有 active request，新请求不会立刻和高 step request 混跑。
- scheduler 选择当前最小 `step_index` 的请求执行。
- 新 admitted request 会先单独或小批 catch up 到同一个 step。
- 当多个 request 的 `step_index` 对齐后，才会进入同一次 `denoise_step`。
- 输出里区分 `NewRequestData` 和已有 request id，避免重复 prepare。

为什么需要 catch up：

- continuous batching 下，请求可能不是同时到达。
- DiT step 不能把 step 3 和 step 7 的 latent 放进同一个 forward。
- catch up 让新请求追上老请求，再开始组 batch。

### 4.3 InputBatch 把 request state 传给 pipeline

文件：`vllm_omni/diffusion/worker/input_batch.py`

关键改动：

- `582`: `states: Sequence[DiffusionRequestState]`
- `590-593`: prompt embeds 相关字段改成 optional。
- `604-612`: `__post_init__` 校验 states 数量和 batch 对齐。
- `645-650`: repack 时保留 selected states。
- `652-669`: rebuild 时保留 selected states。
- `671-720`: `make_batch` 构造 InputBatch 时传入 states。

解释：

- HunyuanImage3 的 DiT inputs 不是简单 `prompt_embeds + latents`，而是包含 tokenizer outputs、attention mask、AR KV、prompt KV cache、scheduler 等 request-local extra。
- 所以 `denoise_step` 必须能拿到每个 request 的完整 state。
- prompt embeds optional 是为了允许 HunyuanImage3 走自己 pipeline 的 model input merge，而不是强塞 generic prompt embed contract。

## 5. CFG 和 batch 维度怎么讲

HunyuanImage3 开 CFG 时，一个请求本身就要跑两条 DiT branch：

- conditional branch：按 prompt 条件生成。
- unconditional / negative branch：作为对照。

然后用公式做 guidance：

```text
noise = uncond + guidance_scale * (cond - uncond)
```

所以 batch 维度不是简单的 request 数，而是：

```text
effective_dit_rows = num_requests * cfg_factor
cfg_factor = 1 if guidance_scale <= 1 else 2
```

例子：

```text
max_num_seqs=1, guidance_scale=2.5
每 step DiT rows = 1 * 2 = 2

max_num_seqs=2, guidance_scale=2.5
每 step DiT rows = 2 * 2 = 4
```

重要口径：

- CFG 不是为了提升 GPU 利用率，它是为了图像质量和 prompt adherence。
- CFG 会增加计算量，因为每个 request 要多一条 branch。
- grouped batching 的收益来自“把多个 request 的 denoise step 合并成一个更大的 DiT forward”，不是把 CFG 成本变没。

## 6. 为什么收益没有翻倍

理论上两个请求组 batch，不等于耗时直接减半。原因有五个：

1. Baseline 已经接近 GPU busy。NVML util P50/P90 接近 100%，说明 DiT forward 本身已经很吃满。
2. CFG 让 baseline 的单请求已经是 2 rows；组两个请求是 4 rows。4 rows 比 2 rows 更大，但不是“两个请求变成一个请求的成本”。
3. VAE decode、请求编排、AR stage 等固定开销没有被 DiT batching 消掉。
4. e2e 场景里 AR 和 DiT 分布在不同 GPU 组，端到端 wall time 受 stage handoff 和流水等待影响。
5. 当前第一版是 correctness-first，没有做 kernel-level padding 优化、MixFusion、异分辨率合批或更激进的 prefetch。

会议口径：

- 这次 PR 的核心价值是“把 DiT 从不能 batch 打通到能 batch”，不是承诺第一版吞吐翻倍。
- 真实性能收益需要继续看大并发、更多 prompt、不同 step 数和 Nsight / DCGM 的 achieved FLOPS。

## 7. 当前数据口径

### 7.0 先读：不同轮次数据不可混写

本节历史数据来自较早的 PR 分支和会议口径；2026-06-05 对 PR #4041 head `8a421a39aeead627ab341aecf088ae6dfae4c2de` 做了另一轮 2 卡 DiT-only 复测，结果是明显退化。以后写 PR 结论时必须把 head sha、远端、YAML、quantization、CFG、prompt 数、steps 和 artifact 目录放在同一段里，禁止把不同轮次的“收益”和“退化”混成一个结论。

### 7.1 DiT-only 性能

口径：NVML 每 200ms 采样一次，只统计 `omni.generate(...)` 期间，不包含模型初始化。这个指标是 GPU busy，不是 MFU。

| Mode | Elapsed | Throughput | Avg GPU util | P50 | P90 | Peak |
|---|---:|---:|---:|---:|---:|---:|
| Baseline max1 | 50.916s | 0.03928 img/s | 98.20% | 99.5% | 100.0% | 100% |
| Grouped max2 | 46.382s | 0.04312 img/s | 97.91% | 100.0% | 100.0% | 100% |

结论：

- DiT-only wall time speedup 约 `1.098x`。
- grouped 的 avg GPU util 略低不代表更慢；吞吐是更高的。
- util 差异在 0.3 个百分点量级，主要受固定低 util 片段、采样窗口和 stage 边界影响。

### 7.2 Official IT2I e2e 性能

| Mode | Elapsed | Throughput | Avg util across 4 GPUs | P50 | P90 | Peak |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 188.001s | 0.01064 img/s | 42.41% | 49.5% | 50.0% | 100% |
| Grouped | 181.551s | 0.01102 img/s | 41.83% | 50.0% | 50.0% | 100% |

DiT GPU 细分：

| Mode | GPU2 avg | GPU2 P50 | GPU3 avg | GPU3 P50 |
|---|---:|---:|---:|---:|
| Baseline | 55.65% | 99% | 55.58% | 99% |
| Grouped | 54.62% | 100% | 54.47% | 100% |

结论：

- e2e speedup 约 `1.036x`。
- e2e 平均 util 低，是因为 AR/DiT 分阶段运行，4 张卡不是全程同时满载。
- DiT GPU 在 DiT 活跃窗口内 P50 接近 100%，说明瓶颈偏 compute-bound。

### 7.3 精度

官方 fixture / official prompt / seed 42 / 50 denoise steps / guidance scale 2.5：

| Request | CLIP image-image | SSIM | PSNR |
|---|---:|---:|---:|
| grouped req0 | 94.4988 | 0.4822 | 14.2763 dB |
| grouped req1 | 94.4988 | 0.4822 | 14.2763 dB |
| single step-wise reference | 94.7905 | 0.4872 | 14.2872 dB |

阈值：

- CLIP >= 85
- SSIM >= 0.20
- PSNR >= 11.0 dB

结论：

- grouped batch 通过官方 accuracy fixture 阈值。
- 两个 request 使用 request-local generator、latents、scheduler；batch composition 不应该改变每个请求自己的随机数和 scheduler state。

### 7.4 PR #4041 head 2 卡 DiT-only 复测（2026-06-05，退化）

这轮是用户指定的最小复测：只跑 DiT、2 卡、2 concurrent prompts。它用于判断 PR #4041 当前 head 在小并发 DiT batch=2 下是否有收益，不等同于上面的历史会议口径。

Scope：

- 远端：`root@47.79.124.13 -p 31449`
- 工作区：`/data/wzr/vllm-omni`
- PR head：`8a421a39aeead627ab341aecf088ae6dfae4c2de`
- base：`origin/main=6cefe913703fa67a0726c327476334fe391154d0`
- 模型：`/data/model/hub/models--tencent--HunyuanImage-3.0-Instruct/snapshots/2ec2c78bee7d4b94157341fba86c4c2c7b1858b2`
- GPU：`CUDA_VISIBLE_DEVICES=5,7`
- 配置：FP8，1024×1024，50 steps，`guidance_scale=1.0`
- 产物：`/data/wzr/pr4041_dit_bench_20260605_164448/summary.json`

| Mode | Elapsed | Throughput | Result |
|---|---:|---:|---|
| baseline `max_num_seqs=1` | `15.5205s` | `0.12886 req/s` | 正常完成 |
| grouped `max_num_seqs=2` + `step_execution=true` | `202.2987s` | `0.00989 req/s` | 正常完成但慢 |

结论：本轮 grouped 吞吐是 baseline 的 `0.0767x`，约慢 `13x`。日志确认 grouped 命中 `batch_size=2` 和 `step execution`；attention backend 是 `FLASH_ATTN`，不是 SDPA fallback；正式日志没有 OOM/Traceback。

复盘口径：小 batch=2/no-CFG 场景下，step execution 的 per-step bookkeeping 成本过高，包括 `InputBatch` merge/split、prompt KV cache capture/restore、attention mask/full_attn_spans padding 和 masked piecewise attention 的逐 row 整理。这个结论要和历史收益数据分开写，不能拿旧收益覆盖当前 head 的退化。

### 7.5 性能差异定位：#3766 有收益、#4041 退化的关键分叉

最小对照已经把主因收敛到 attention path：

| Mode | Attention | Elapsed | Artifact |
|---|---|---:|---|
| request-mode baseline | default | `15.5205s` | `/data/wzr/pr4041_dit_bench_20260605_164448/` |
| #4041 grouped | default `FLASH_ATTN` masked piecewise | `202.2987s` | `/data/wzr/pr4041_dit_bench_20260605_164448/` |
| #4041 grouped | forced `TORCH_SDPA` | `15.9735s` | `/data/wzr/pr4041_grouped_sdpa_20260605_172338/` |

#3766 的 attention 策略是：`full_attn_spans` 非同构或 row-specific padding 不能被 piecewise FA 精确表达时，设置 / 传播 `requires_sdpa_for_full_attn_spans`，最后在 attention layer 回退 SDPA。#4041 的策略是：删除 Hunyuan transformer 里的 SDPA escape flag，把 `attn_mask` 传给 `piecewise_attn`，在 piecewise FA 里逐 row 做 mask normalization、baseline mask、padding keep、`nonzero` / `.tolist()` / `index_select` 和 span compaction。

因此当前证据支持：

- #4041 退化主因不是“step execution 一定慢”，因为同一 grouped path 强制 SDPA 后基本回到 baseline。
- #3766 有收益的关键不是架构更正确，而是它避开了 #4041 的 masked piecewise FA per-row compaction 热路径。
- 如果继续推进 #4041，要么恢复 #3766 式 SDPA fallback 作为性能 guard，要么把 masked piecewise FA 改成真正批量化 / kernel 化，至少不能在每层每 step 做 Python `.tolist()` 和 per-row `index_select`。

补充：2026-06-05 按用户要求在新目录 `/data/wzr/pr3766_run_20260605/` 复跑 #3766，同一台机器、2 卡 DiT-only、FP8、no-CFG、同 prompts/50 steps。结果没有复现旧 PR body 的 DiT-only speedup：

| Mode | Ref | Elapsed | Throughput |
|---|---|---:|---:|
| baseline | #3766 base `67bb9b4a` | `15.2753s` | `0.13093 req/s` |
| grouped | #3766 head `a8d532c` | `15.8363s` | `0.12629 req/s` |

artifact：`/data/wzr/pr3766_run_20260605/pr3766_dit_bench_20260605_182600/`

本轮 grouped 日志确认 `batch_size=2`，并触发 #3766 的 `Falling back to SDPA`。所以更准确的说法是：#3766 的 fallback 是性能保护阀，避免 #4041 那种 masked FA 大退化；但在当前 2 卡 no-CFG FP8 口径下，fallback 本身并不会稳定带来 grouped 收益。

补充 2：2026-06-08 按用户要求把 `image_base_size` 改为 `512`，并 sweep `batch=2,4,6,8`。本轮在同一 #3766 独立目录里新建 `/data/wzr/pr3766_run_20260605/model_image_base_512`，通过 symlink 复用原 snapshot 权重，只覆盖 `config.json` 写入 `"image_base_size": 512`；benchmark prompt 也显式带 `height=512`、`width=512`、`image_base_size=512`。

artifact：`/data/wzr/pr3766_run_20260605/pr3766_image_base512_batch_sweep_20260608_105822/`

| Batch | Baseline elapsed | Grouped elapsed | Speedup |
|---:|---:|---:|---:|
| 2 | `9.7505s` | `6.1950s` | `1.5739x` |
| 4 | `19.9516s` | `7.5521s` | `2.6419x` |
| 6 | `30.1161s` | `10.1415s` | `2.9696x` |
| 8 | `38.8501s` | `13.3199s` | `2.9167x` |

这轮 grouped 日志分别确认 `batch_size=2/4/6/8`，并全部触发 #3766 的 `Falling back to SDPA`。baseline 和 grouped 日志都确认 `guidance_scale <= 1.0`，没有走双向 CFG denoise。结论要更新：`1024x1024, batch=2` 没收益不代表 #3766 的旧收益不存在；在 `image_base_size=512` 且 batch 放大后，baseline 基本按请求数线性增长，而 grouped 能把多个请求合进同一 denoise step，SDPA fallback 成本被 batch 摊薄，所以收益重新出现。

补充 3：2026-06-08 按用户要求对新的 PR #4041 跑同样的 `image_base_size=512`，并拆成默认 FA 和强制 SDPA 两个口径。环境沿用 `/data/wzr/vllm-omni`，base 是 `6cefe913703fa67a0726c327476334fe391154d0`，PR head 是 `8a421a39aeead627ab341aecf088ae6dfae4c2de`，GPU 是 `CUDA_VISIBLE_DEVICES=5,6`，同样是 DiT-only、FP8、50 steps、`guidance_scale=1.0`。

artifact：`/data/wzr/pr4041_image_base512_fa_sdpa_sweep_20260608_113335/`

| Batch | Baseline elapsed | #4041 grouped FA | FA speedup | #4041 grouped SDPA | SDPA speedup |
|---:|---:|---:|---:|---:|---:|
| 2 | `10.1038s` | `21.5573s` | `0.4687x` | `5.7027s` | `1.7718x` |
| 4 | `20.4795s` | `39.1635s` | `0.5229x` | `8.0799s` | `2.5346x` |
| 6 | `32.3690s` | `55.8302s` | `0.5798x` | `10.2475s` | `3.1587x` |
| 8 | `40.3558s` | `73.1498s` | `0.5517x` | `13.8057s` | `2.9231x` |

这轮日志确认：默认 grouped 是 `FLASH_ATTN`，强制口径是 `SDPA`，grouped 分别命中 `batch_size=2/4/6/8`，且没有 classifier-free guidance。人话结论：新 PR 不是没有 group 收益，强制 SDPA 时收益和 #3766 的 512 sweep 是同一量级；问题是默认 FA 口径把收益吞了，FA 比 SDPA 慢 `3.78x-5.45x`。

更准确的人话：#4041 里 scheduler 确实把请求 group 起来了，但默认 FA 的 masked piecewise 分支又在 attention 内部按 row 拆开。代码路径是 `flash_attn.py` 把 `attn_mask` 传进 `piecewise_attn`，然后 masked 分支 `for row in full_attn_spans`，每行单独 `nonzero` / `.tolist()` / `index_select` / `_piecewise_attn_grouped(batch=1)` / `index_copy_`。所以这里不是“batch 进 FA kernel 后没赚到”，而是根本没有保住 batched attention 的执行形态。

补充诊断：b2 / 5-step 计数里，两个 worker 合计 `512` 次 `piecewise_attn` 全部是 masked，`896` 个 row 里 `576` 个 row 的 mask 等价于 baseline 且无 padding，`384` 个 multi-row call 里有 `192` 个 call 的 row signature 完全相同。也就是说，这条实现路径连“其实不用 compact / 可以继续 grouped”的情况也统一走 per-row compaction，确实偏笨。

5-step profile 进一步细化了“FA 额外耗时从哪来”：

- artifact：`/data/wzr/pr4041_piecewise_profile_20260605_174838/profile_summary.json`
- measured elapsed：`20.7378s`
- `piecewise_attn` 顶层跨 worker 聚合：`512 calls / 51.7708s`
- helper 计时很小：`_piecewise_mask 0.343s`、`_padding_keep_masks 0.263s`、`_compact_spans 0.236s`、`_piecewise_attn_grouped 0.496s`

这说明大头不在 mask 公式本身，而在 masked path 顶层未单独包裹的同步/索引区：`torch.nonzero`、CUDA tensor `.tolist()`、Python `kept_positions.index(...)`、per-row `index_select` / `index_copy_`。尤其 `nonzero` 和 `.tolist()` 会让 GPU 流和 host 同步，放到每层每 step 后会非常贵。

## 8. 常见问题和回答

### Q1: 现在是不是只能相同 prompt 才能组 batch？

不是。当前代码支持不同 prompt token length，通过 `_right_pad_step_tensors` 做 right padding。

真正要求相同的是 batch compatibility：

- 同分辨率。
- 同 `num_inference_steps`。
- 同 CFG 模式 / guidance 兼容。
- 同并行配置。
- 同 step index。

prompt 不同可以组；prompt 导致的 sequence length 不同也可以组。不能组的是 shape 或执行语义不兼容。

### Q2: encode 是串行的，为什么还要管 prompt length？

encode 确实是逐 request 做的，但 DiT forward 前要把每个 request 的 `input_ids`、attention mask、position ids、KV metadata 合成一个 batch tensor。

如果不 padding，不同 token length 的 tensor 不能 `torch.cat`。这次 PR 已经补了 right padding，所以不再要求 prompt token length 完全相同。

### Q3: 为什么不直接改 `DiffusionEngine` 的 max_num_seqs 限制？

因为 request-mode 的语义是一个 request 一次跑完整 denoise loop。它没有每 step 调度点，也没有 request-local scheduler state 的生命周期管理。

正确入口是 step-wise execution：

- scheduler 每 step 选一组 compatible requests。
- pipeline 每 step 只做一次 DiT forward。
- scheduler 再把 noise_pred 分别写回每个 request。

这和 continuous batching 的架构一致。

### Q4: AR 本来支持 batch，为什么 DiT 还要改？

AR batch 只覆盖 AR stage。AR 结束后进入 DiT 时，旧 DiT path 还是 request-mode，`max_num_seqs > 1` 会被限制或退化。

这次改的是 AR->DiT 交接之后的 DiT denoise loop，让 DiT stage 也能 continuous batching。

### Q5: CFG 是不是为了提升 GPU 利用率？

不是。CFG 是图像质量机制，用 conditional 和 unconditional 的差值增强 prompt adherence。

它通常会让图像更贴 prompt，但代价是每个 request 多一条 DiT branch。GPU util 变高只是计算量增加的副作用，不是 CFG 的目标。

### Q6: 既然两个请求组 batch，为什么收益不接近 2x？

因为原来单请求开 CFG 时已经是 2 rows；两个请求组 batch 是 4 rows。DiT 的矩阵计算变大了，但不是把第二个请求免费塞进去。

另外 VAE decode、AR stage、调度、通信、stage handoff 不会因为 DiT batch 直接减半。

### Q7: decode 开销不是一样吗？那为什么还影响端到端收益？

对，decode 对每张图仍要做。DiT grouped batching 主要减少的是 denoise loop 中的串行 request 执行和 kernel launch / scheduler 往返。

如果 e2e 里 decode、AR 或 handoff 占比高，那么 DiT 提速会被这些固定开销稀释。

### Q8: 为什么 grouped GPU util 可能略低，但 throughput 更高？

NVML util 是采样窗口里的 busy 百分比，不是实际 FLOPS。它看不到 kernel 效率，也看不到同样 busy 下每秒处理了多少 token / latent rows。

grouped 可能用更短时间完成任务，但因为固定低 util 片段占比、采样窗口边界不同，平均 util 略低。最终判断吞吐要看 wall time 和 img/s。

### Q9: 这个 GPU util 能说明算力利用率吗？

不能完全说明。NVML util 只能说明 GPU 是否 busy，不等于 MFU / achieved FLOPS。

如果会议上有人追问算力利用率，回答应该是：

- 当前 PR 提供的是 NVML busy 指标。
- 真正 MFU 需要 Nsight Compute / Nsight Systems / DCGM profiling，按 DiT FLOPs 和实际运行时间计算 achieved FLOPS。
- 所以 PR 里不能用 NVML util 声称“算力利用率 98%”，只能说“NVML GPU busy 约 98%”。

### Q10: 为什么 scheduler 必须 per-request deepcopy？

diffusers scheduler 内部有 mutable `_step_index`。如果多个 active request 共享 `self.scheduler`，一个请求 step 之后会推进全局 step index，另一个请求就会错位。

所以 `prepare_encode` 里 `deepcopy(self.scheduler)`，`step_scheduler` 只 mutate `state.extra["scheduler"]`。

### Q11: 为什么 latents 要强制 fp32？

scheduler step 输出是 fp32。新请求刚 prepare 出来的 latent 可能是 bf16。

continuous batching 允许 staggered request catch up。如果一个老请求 latent 是 fp32，新请求 latent 是 bf16，合批时 dtype 会不一致。统一 fp32 是为了保证后续 `InputBatch` 合并稳定。

### Q12: 为什么现在不做 MixFusion / 异分辨率？

异分辨率不是简单 padding prompt。它涉及 latent shape、image token grid、RoPE、attention mask、KV cache layout、scheduler output shape。

第一版目标是同分辨率 grouped batching，先把 DiT step-wise path 打通。MixFusion 可以在这个基础上继续做，但不应该和第一版 correctness 混在一起。

### Q13: 失败时会不会 silent fallback 到单请求？

不会。设计上遇到不支持组合直接 `ValueError`。

原因是 silent fallback 会让用户以为 `max_num_seqs=2` 生效，实际没有组 batch，性能数据和行为判断都会被污染。

### Q14: 和 Qwen-Image 那种 batching 逻辑是否一致？

原则一致：相同 sampling / 兼容参数可以组 batch，不要求 prompt 字符串相同。

HunyuanImage3 的复杂点在于：

- 有 AR->DiT KV reuse。
- 有 generalized causal attention mask。
- 有 CFG rows。
- DiT forward 会更新 request-local model kwargs / prompt KV cache。

所以实现上需要更多 state split / merge，但 batch gating 的目标和 Qwen-Image 是一致的。

### Q15: 精度会不会因为组 batch 变化？

理论上不应该，因为：

- seed / generator 是 request-local。
- scheduler 是 request-local。
- initial latents 是 request-local。
- prompt KV / AR KV 都拆回 state，不依赖 batch 邻居。

但 floating point kernel 在不同 batch shape 下可能有极小数值差异，所以用 CLIP / SSIM / PSNR 做阈值验证，而不是承诺 bitwise identical。

## 9. 会议讲法建议

开场三句话：

1. 这次不是改 request-mode clamp，而是把 HunyuanImage3 DiT 接到现有 step-wise diffusion continuous batching。
2. 每个 request 的 encode、scheduler、KV cache 都是 request-local；只有当前 denoise step 的 DiT forward 做 transient merge。
3. 第一版刻意保守，只承诺同分辨率同参数 grouped batching，不把 MixFusion 和异分辨率混进来。

被问性能时：

- 先说 DiT-only speedup `1.098x`，e2e official IT2I speedup `1.036x`。
- 再解释 baseline DiT GPU busy 已经很高，CFG 单请求已经是 2 rows，所以第一版收益不会翻倍。
- 最后强调这次价值是“从不能 batch 到能 batch”，后续性能空间在 MixFusion、更多并发、kernel profiling 和 stage overlap。

被问正确性时：

- 先说 per-request scheduler deepcopy，避免 `_step_index` 串。
- 再说 AR KV / prompt KV 都 snapshot 到 state，forward 前 merge，forward 后 split。
- 最后说 unsupported combo 早失败，不 silent fallback。

## 10. 复现命令口径

PR 里的 e2e 复现应该讲“怎么测”，不要堆 UT：

```text
remote: root@47.79.124.13 -p 31140
workspace: /home/wzr/wt-codex-hunyuanimage3-step-batch
python: /root/hsliu/.venv/bin/python
offline env:
  unset TRANSFORMERS_CACHE HF_HUB_CACHE
  export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
```

测试形态：

- AR on GPUs 0,1。
- DiT on GPUs 2,3。
- official Tencent demo assets。
- official prompt from `tests/e2e/accuracy/test_hunyuan_image3.py`。
- seed 42。
- 50 denoise steps。
- guidance scale 2.5。
- DiT `step_execution=True`。
- DiT `max_num_seqs=2`。
- `diffusion_batch_size=2`。

发请求口径：

- baseline：同 official IT2I 输入，`max_num_seqs=1`，两条请求串行。
- grouped：同 official IT2I 输入，`max_num_seqs=2`，两条请求同时进入 DiT。
- 对输出图和 `tests/e2e/accuracy/assets/hunyuan_image_ref.png` 计算 CLIP image-image、SSIM、PSNR。

## 11. 可以主动承认的局限

- 当前性能数据是 NVML busy，不是 MFU。
- 当前收益在 2-request official e2e 上不大，主要因为 baseline DiT 已经很忙，且 CFG / AR / VAE / handoff 稀释收益。
- 当前不支持异分辨率 / MixFusion / SP / CFG parallel。
- 当前是 opt-in experimental path，默认 deploy 不改。

这几个局限建议主动讲。主动讲清楚，会议里就不会被别人拿这些点反过来质疑“是不是夸大了”。
