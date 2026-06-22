# HunyuanImage3 AR graph online perf 快速结论（2026-06-09）

目标：观察 AR graph online 路径中 decode step 间隙和短 memcpy 现象，尝试优化 `hunyuan_image3_ar` 单阶段 `vllm serve` + `vllm bench serve` 路径。

关键 runbook：

- 远端：`root@106.15.124.84:31342`
- 工作仓：`/home/wzr/vllm-omni`，该仓有 serving 侧 dirty patch；clean worktree 启动同命令会 400，不能拿 clean worktree 直接做 online 对照。
- AR graph deploy：`enforce_eager: false`，`devices: "0,1"`，外层 `CUDA_VISIBLE_DEVICES=2,3` 映射物理 GPU 2/3。
- 必须用本地模板绝对路径：`--chat-template /home/wzr/vllm-omni/hunyuan_image3_i2t.jinja`。
- 共享机器上 GPU0 有其他用户进程；本轮只用 GPU2/3，结束后确认两张卡回到 `4 MiB`。
- 大模型启动前设置 `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`，日志应出现 snapshot 替换，避免网络/下载抖动。

本轮误判和排除：

- 试过在 `OmniGPUModelRunner._preprocess` 对 decode-only batch 跳过 multimodal embedding path，直接用 `input_ids` 进模型。这个优化 **不可用**。
- 证据：同一 dirty serving、同一 bench 命令、同一 GPU、同一 seed 下：
  - fast path：`Successful requests=1`，但只生成 `3` tokens，`Mean TPOT=1795.63 ms`。
  - baseline：生成 `294` tokens，`Mean TTFT=792.78 ms`，`Mean TPOT=12.99 ms`，`Output throughput=63.93 tok/s`。
- 结论：HunyuanImage3 AR 的 multimodal input/kwargs 路径在 decode 阶段仍然是语义契约的一部分，不能为了减少 `embed_input_ids -> inputs_embeds.copy_` 把 supports-mm 模型切到普通 text-only `input_ids` 路径。

启动耗时拆解：

- baseline 对照：`Model loading took 78.71 GiB memory and 37.95s`，`Graph capturing finished in 7s`，`AsyncOmniEngine initialized in 88.56s`。
- fast path 首次修改 runner 后：`torch.compile took 51.56s`，`AsyncOmniEngine initialized in 166.40s`。这不是“图模式本身 15 分钟”，而是代码变更触发新的 torch compile cache key；恢复 baseline 后 cache 命中，engine init 回到约 1.5 分钟。
- 首请求仍有 Triton JIT during inference：`_compute_slot_mapping_kernel`、`kernel_unified_attention`、`fused_moe_kernel`。这会污染 TTFT/首轮 trace；正式性能测量应先跑 warmup 请求，或者把这些形状纳入 engine warmup，再开始 profiler/benchmark 主请求。

后续正确优化方向：

1. 不再改 AR decode 输入契约；任何跳过 MM embedding 的方案必须先做 token 序列 parity，至少比较 `ignore_eos=True` 下生成 token 数和前几十个 token。
2. 优先优化首请求 JIT：复用已有 `dummy_run` / graph capture / serving warmup 机制，覆盖真实 AR image prompt 的 slot mapping、attention、MoE 形状。
3. profiling 要在 warmup 请求之后打开，在目标请求完成后关闭；否则 trace 会主要记录启动、compile、空闲或无效短输出。

## AR graph online profiling 有效 trace（2026-06-09）

本轮重新按 online 正确口径抓 trace：先启动 `vllm serve`，先跑 warmup 请求，warmup 完成后调用 profiler start，请求完成后 stop profiler，最后释放本轮进程组。

产物：

- 远端目录：`/tmp/hy3_ar_gap_profile_20260609_044200/`
- trace：`profiler/20260609-044408_stage0_rank0_1780980248/trace_rank0.json.gz`（约 95 MB gz）、`profiler/20260609-044408_stage0_rank1_1780980248/trace_rank1.json.gz`（约 92 MB gz）
- 分析汇总：`ar_gap_trace_analysis.txt`、`ar_gap_key_events_rank0.txt`
- 资源释放：结束后 `GPU0=0 MiB, GPU1=0 MiB, GPU2=4 MiB, GPU3=4 MiB`

启动与请求口径：

- `Model loading took 78.71 GiB memory and 40.23s`
- `torch.compile took 3.55s`
- `Graph capturing finished in 8s`
- `AsyncOmniEngine initialized in 89.72s`
- warmup 请求在 profiler 外：生成 `294` tokens，`TTFT=821.81ms`，`TPOT=11.28ms`，`output throughput=71.24 tok/s`
- target 请求在 profiler 内：生成 `294` tokens，`TTFT=347.40ms`，`TPOT=13.71ms`，`output throughput=67.34 tok/s`

trace 结论：

- rank0/rank1 都有约 `5.0M` trace events，`kernel` 约 `520k`，`gpu_memcpy` 约 `7,845`。
- 口径修正：不能把 `gpu_user_annotation` 当 GPU busy；它只是 NVTX 范围，算进去会把 step 内空白抹掉。真实 GPU busy 只统计 `kernel/gpu_memcpy/gpu_memset`。
- 以外层 `execute_context_0(0)_generation_1(1)` user annotation 作为 decode step window：rank0/rank1 都有 `511` 个 outer generation steps。
- rank0：outer step `width p50=6.900ms`、`gpu_busy p50=5.344ms`、`gpu_idle p50=1.558ms`、`gpu_idle p90=1.631ms`。
- rank1：outer step `width p50=6.988ms`、`gpu_busy p50=5.448ms`、`gpu_idle p50=1.542ms`、`gpu_idle p90=1.576ms`。
- 每个 step 里 memcpy 很多但很短：rank0 `count p50=56`、`memcpy time p50=152.2us`；rank1 `count p50=57`、`memcpy time p50=141.7us`。因此用户看到的短 copy 是 gap 前后的伴随事件，不是主耗时本体。
- 最大 step 内 GPU 空白常出现在 `Memcpy DtoD` 之后、下一个 `triton_red_fused_rms_norm_0` 之前：rank0 最大 `4.892ms`，rank1 最大 `4.207ms`。
- rank0 step 132 细查：`Memcpy DtoD` 在 `+4.921ms` 结束，下一段 `rms_norm` kernel 到 `+9.814ms` 才开始；中间 CPU 侧有 `aten::item/_local_scalar_dense` 同步，以及 `cudaGraphLaunch` / `torch/cuda/graphs.py: replay`。
- CPU overlap 大头：
  - rank0：`cudaEventSynchronize 2.585s`、`aten::item 1.600s`、`aten::_local_scalar_dense 1.599s`、`cudaStreamSynchronize 1.590s`、`cudaGraphLaunch 672.940ms`。
  - rank1：`aten::item 1.692s`、`aten::_local_scalar_dense 1.691s`、`cudaStreamSynchronize 1.682s`、`cudaGraphLaunch 665.505ms`。
- key parent-chain 追踪修正：`aten::item` 的父栈不是 sampler，而是 `vllm_omni/worker/gpu_model_runner.py:1437 _preprocess -> hunyuan_image3.py:1994 embed_input_ids`，具体代码是 `timestep_mask.sum().item()`。这个每个 decode step 都会读 GPU scalar 回 CPU。
- `aten::copy_` 虽然有上万次，但 rank0 step overlap 只有 `96.043ms`，rank1 只有 `90.338ms`。优化 copy 只能拿小头；优先级低于移除 `timestep_mask.sum().item()` 和确认 `cudaGraphLaunch` overhead。

当前优化边界：

1. 不要再改 decode 输入契约。直接把 HunyuanImage3 AR decode 从 MM embedding path 切成 text-only `input_ids` 已实测破坏输出。
2. 第一优先级是消除 `embed_input_ids` 里的 `timestep_mask.sum().item()`。推荐最小改法：无条件构造 `timestep_emb(0)`，用 GPU `torch.where(timestep_mask.unsqueeze(-1), timestep_embed, inputs_embeds)` 做替换，避免 CPU 分支读 GPU scalar。
3. 第二优先级是确认 `cudaGraphLaunch` 为什么每 step 累计约 `1.3ms` 平均 CPU runtime，且大 gap 里 kernel 到 graph launch 结束才开始。需要对比 patch 后 trace，分清是 `.item()` 同步拖住 graph launch，还是 graph replay 本身仍有独立提交开销。
4. 任何改法必须保留 294-token 输出 parity，再看 TTFT/TPOT 和 step idle。远端本轮尝试验证 patch 时 GPU 被 `/rebase/vllm-omni/tests` 的他人进程占满，未跑成；远端单文件已还原。

## `timestep_mask.sum().item()` patch 对照（2026-06-09）

本地分支：`D:\vllm-omni\wt-ar-step-gap-opt-main`，commit `8bc0bcc9e [Perf] Avoid timestep mask scalar sync`。

改动：

```python
timestep_mask = input_ids == self._timestep_token_id
timestep_input = torch.zeros((1,), device=inputs_embeds.device, dtype=inputs_embeds.dtype)
timestep_embed = self._timestep_encode(timestep_input).to(inputs_embeds.dtype)
inputs_embeds = torch.where(timestep_mask.unsqueeze(-1), timestep_embed, inputs_embeds)
```

远端验证：

- artifact：`/tmp/hy3_ar_gap_profile_20260609_064355/`
- 同一 dirty serving worktree，仅临时 checkout 单文件 patch；跑完后已 `git checkout HEAD -- vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py` 还原。
- 输出 parity：warmup / target 都生成 `294` tokens。
- 资源释放：结束后四张 GPU 均回到 `4 MiB`。

请求指标：

| Window | Benchmark duration | TTFT | TPOT | Output throughput | Notes |
|---|---:|---:|---:|---:|---|
| warmup outside profiler | `4.03s` | `790.75ms` | `11.05ms` | `72.96 tok/s` | 可近似看 no-profile 请求 |
| target inside profiler | `5.08s` | `336.47ms` | `16.19ms` | `57.87 tok/s` | profiler window trace 明显更重，p99 ITL `47.26ms` |

trace 对照：

| Metric | Baseline rank0 | Patch rank0 | Baseline rank1 | Patch rank1 |
|---|---:|---:|---:|---:|
| `aten::item/_local_scalar_dense` | `~1.60s / 512 calls` | not present in key events | `~1.69s / 512 calls` | not present in key events |
| outer step width p50 | `6.900ms` | `4.593ms` | `6.988ms` | `4.562ms` |
| GPU busy p50 | `5.344ms` | `4.486ms` | `5.448ms` | `4.478ms` |
| GPU idle p50 | `1.558ms` | `56.9us` | `1.542ms` | `47.9us` |
| GPU idle p90 | `1.631ms` | `3.949ms` | `1.576ms` | `3.662ms` |
| `cudaGraphLaunch` overlap | `672.940ms` | `671.170ms` | `665.505ms` | `691.184ms` |

结论：

- patch 有效消除了每步 `timestep_mask.sum().item()` 造成的 scalar sync，step idle 中位数从 `~1.5ms` 降到 `~50us`。
- patch 没解决 tail gap：p90 仍是 `3-4ms`，剩余大头集中在 `cudaGraphLaunch` / graph replay 提交阶段，最大 gap 仍常出现在 `Memcpy DtoD` 后、下一段 `rms_norm` kernel 前。
- target profiler 指标反而变差，不能直接说明生产性能倒退；warmup/no-profile 请求略好，但需要再做无 profiler 多轮 bench 才能定量。当前结论只到“同步点定位和中位 idle 改善成立，tail 仍未解决”。

## AR graph no-profiler patch 对照（2026-06-09）

用户指出正确定量口径应先看不带 profiler 的 online benchmark。补跑同机同脚本 no-profiler 对照：

- baseline artifact：`/tmp/hy3_ar_gap_noprofile_baseline_20260609_080810/`
- patch artifact：`/tmp/hy3_ar_gap_noprofile_patch_20260609_081248/`
- GPU：`CUDA_VISIBLE_DEVICES=2,3`
- deploy：`hunyuan_image3_ar`，`enforce_eager: false`，TP=2，`devices: "0,1"`
- benchmark：warmup `num_prompts=1`，target `num_prompts=5`，`random-mm`，`1024x1024x1 image`，`random_input_len=256`，`random_output_len=512`，`max_concurrency=1`，`ignore_eos`
- 远端只临时 checkout 单文件 patch；跑完后已恢复 `hunyuan_image3.py`，GPU2/3 回到 `4 MiB`

结果：

| Metric | Baseline | Patch | Delta |
|---|---:|---:|---:|
| Startup wall | `126s` | `126s` | flat |
| Model loading | `38.51s` | `41.35s` | noise / IO |
| torch.compile | `14.29s` | `14.76s` | both recompiled |
| Graph capture | `10s` | `9s` | flat |
| Engine init | `115.20s` | `115.30s` | flat |
| Benchmark duration | `20.08s` | `19.17s` | `-4.5%` |
| Output throughput | `65.65 tok/s` | `68.76 tok/s` | `+4.7%` |
| Mean TTFT | `765.88ms` | `651.06ms` | `-15.0%` |
| Mean TPOT | `14.06ms` | `13.77ms` | `-2.1%` |
| Mean ITL | `6.35ms` | `6.22ms` | `-2.0%` |
| P99 ITL | `7.74ms` | `7.65ms` | `-1.2%` |

结论更新：

- `timestep_mask.sum().item()` patch 在真实 no-profiler 路径上也有小幅收益：吞吐约 `+4.7%`，TPOT/ITL 约 `2%` 改善。它不是纯 trace artifact。
- 收益不大，和 trace 结论一致：它消掉的是每步 scalar sync 的中位 idle，但 tail gap 仍在 `cudaGraphLaunch` / graph replay 提交处。
- 两次启动都约 `126s`，并且日志都出现 “Source code has changed since the last compilation. Recompiling the model.”。这解释了本轮启动没有接近理想 `~90s`：baseline/patch 来回 checkout 改源文件会打掉 AOT cache 命中。稳定 benchmark 不要在同一个 worktree 上频繁来回改源码；应固定两个 worktree/两个 cache key，或服务复用后只重启必要对照。

下一步追法：

1. 不再围绕短 `Memcpy DtoD` 做主优化；它每步总量只有百微秒量级，主要是 gap 边界信号。
2. 用 patch 版本继续抓带 stack trace 的小窗口，只看 p90/p99 大 gap：把每个大 gap 前后的 CPU 栈和 `cudaGraphLaunch` duration 拉出来，确认是 graph replay 提交慢、CPU 调度被阻塞，还是某个 replay 前准备逻辑仍在同步。
3. 再做一个“服务不重启”的复用测法：同一 server 连续 warmup + target 3 轮，排除 engine 冷启动、compile cache、首次 JIT 对请求吞吐的影响。
4. 如果要继续写代码，优先级是把 graph replay 前的同步点做 census：搜索 decode path 里的 `.item()`、`.tolist()`、`nonzero`、`cudaStreamSynchronize`、`cudaEventSynchronize`，逐个用 trace parent-chain 证明是否落在 step gap 内；没有 trace 证据的不改。

## AR graph tail gap 继续追踪（2026-06-10）

新增只读分析脚本：

- `.scratch/analyze_ar_launch_cadence_stream.py`
- patch trace 输出：`.scratch/ar_launch_cadence_stream_patch_20260610.txt`
- baseline trace 输出：`.scratch/ar_launch_cadence_stream_baseline_20260610.txt`

这轮追踪回答“用户看到的每个 decode step 中 3 次短 memory copy 后 GPU 空闲，到底是不是 copy 本身导致”。结论是：短 `Memcpy DtoD` 是 graph replay 前的边界信号，不是主耗时本体；真正覆盖空白的是 `cudaGraphLaunch`。

关键证据：

| Trace | Rank | gap p50 | gap p90 | gap p99 | `gap>=1ms` steps | launch p50 | launch p90 | launch p99 | launch sum |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0 | `1.415ms` | `1.470ms` | `3.392ms` | `489/511` | `1.216ms` | `1.250ms` | `3.192ms` | `672.940ms` |
| baseline | 1 | `1.400ms` | `1.429ms` | `3.338ms` | `489/511` | `1.205ms` | `1.231ms` | `3.142ms` | `665.505ms` |
| patch | 0 | `1.4us` | `1.427ms` | `3.127ms` | `118/511` | `1.217ms` | `1.277ms` | `3.036ms` | `671.170ms` |
| patch | 1 | `0.3us` | `1.411ms` | `2.960ms` | `122/511` | `1.233ms` | `1.677ms` | `3.041ms` | `691.184ms` |

解释：

- baseline 里几乎每步都是 `>=1ms` gap，是 `timestep_mask.sum().item()` 把 graph replay 前的等待变成常态。
- patch 后慢 gap 数从 `489/511` 降到约 `120/511`，说明 scalar sync 已经被消掉；剩下的 p90/p99 tail 不是 patch 新引入的。
- patch 里 `gap>=1ms` 的总 gap 基本由 launch 覆盖：
  - rank0：`gap_sum=184.456ms`，`launch_sum=171.808ms`
  - rank1：`gap_sum=189.324ms`，`launch_sum=182.378ms`
- 所有 top slow rows 都是同一个 GPU 边界：`Memcpy DtoD (Device -> Device)` 后，下一段 `triton_red_fused_rms_norm_0` 前。
- 慢 step index 的 diff 以 `3` 居多，但 `mod3` 不集中到单一余数；不能写成“每第 3 个 AR token 触发特殊逻辑”。更准确说法是：慢 launch 在一串 decode step 中高频、跨 rank 同步出现，且不是 Hunyuan sampler 的 ratio/special-token 分支。

已排除的替代配置：

1. `CUDAGRAPH_MODE=PIECEWISE`
   - artifact：`/tmp/hy3_ar_gap_noprofile_patch_piecewise_20260609_162328`
   - target 生成 `1511` tokens（不是 FULL patch 的 `1318`），吞吐 `59.90 tok/s`，慢于 patch/FULL 的 `68.76 tok/s`
   - 启动更慢：`torch.compile 48.78s`，engine init `157.97s`
   - 结论：PIECEWISE 在这条 AR online path 上不是可替换优化，且输出长度不对齐。
2. `disable_custom_all_reduce: true`
   - artifact：`/tmp/hy3_ar_gap_noprofile_patch_disable_custom_ar_20260609_163343`
   - target 生成 `1318` tokens，对齐 patch/FULL
   - 吞吐 `65.81 tok/s`，慢于 patch/FULL 的 `68.76 tok/s`
   - 结论：禁用 custom all-reduce 不是收益项；它可以排除 custom AR 是主要生产优化方向，但仍可再抓一次 trace 验证 tail 是否变化。

当前最可信的机制模型：

1. HunyuanImage3 AR comprehension deploy 没有 `has_preprocess`，decode 固定走 multimodal model 的 `inputs_embeds` 路径。
2. 每步 `_preprocess` 先用 `embed_input_ids` 算 embedding，再 copy 到 graph static buffer。
3. copy 本身只有百微秒级，但 copy 完之后必须 CPU 发起 `cudaGraphLaunch`，这段 launch 在部分 step 里变成 `1.4-3.8ms`，GPU 就空着等第一段 graph kernel（通常是 `rms_norm`）开始。
4. 直接把 decode-only 强切 text-only `input_ids` 路径已实测破坏输出（只生成 3 tokens），所以不能靠绕过 MM embedding contract 硬省 copy。

为什么不能“一行切 input_ids”：

- upstream vLLM 对 prompt-embeds 路径已经写了同类 TODO：理想优化是“双编译 CUDA graph，一份 `input_ids`，一份 `inputs_embeds`”。
- 当前 `CUDAGraphWrapper.concrete_cudagraph_entries` 只按 `BatchDescriptor` 缓存；`BatchDescriptor` 来自 token/req/lora/shape，不包含 `input_ids` vs `inputs_embeds` 这种输入模式。
- capture 时虽然记录了 tensor input addresses，但 replay 不会因为输入语义变化自动换图；debug 模式才会 assert 地址一致。
- 因此，粗暴 runtime 切到 `input_ids` 可能复用原先 `inputs_embeds` FULL graph entry，语义不成立。正确探索方向是扩展 graph key / 双 wrapper / 双 runtime path，而不是绕过 `_preprocess`。

下一步只做两类事：

1. **低风险可合并**：保留 `timestep_mask.sum().item()` patch。它有输出 parity，no-profiler 吞吐 `+4.7%`，是目前唯一干净收益。
2. **探索性优化**：研究“multimodal decode-only 双图 / input_ids graph”是否能语义等价地把 embedding 放回 graph。最低验证门槛是同一 prompt 下 token 数、前几十个 token、TTFT/TPOT 都对齐；否则不进 benchmark。

不要继续投入的方向：

- 不要围绕那几次短 DtoD copy 本身做主优化；trace 已经显示主空白不在 copy duration。
- 不要把 PIECEWISE 当生产替代；它更慢且输出不对齐。
- 不要只看 profiler target 的 TPOT 下结论；正式性能结论用 no-profiler target，多轮重复后再写。

## AR graph perf PR 证据口径（2026-06-12）

这轮最终用于 PR 的证据分三层，不要混报：

1. **算子/同步点证据**：来自 request-window profiler trace，用来证明 `timestep_mask.sum().item()` 是真实 GPU scalar sync。
2. **端到端性能证据**：来自 no-profiler online benchmark，用来证明收益不是 profiler artifact。
3. **精度证据**：来自 AR-only prefix accuracy，用来证明改动没有破坏 AR 输出语义。

最终 PR #4363 的可复用写法：

- server path：`vllm serve` + `hunyuan_image3_ar` deploy + `enforce_eager: false`
- bench script：`vllm bench serve`
- endpoint/backend：`/v1/chat/completions` + `openai-chat-omni`
- workload：`random-mm`，`num_prompts=10`，`max_concurrency=1`，每请求 1 张 `1024x1024` 图片，`input_len=256`，`output_len=512`，`temperature=0`，`ignore_eos=True`
- request body override：`{"modalities":["text"],"bot_task":"think"}`

PR 性能表要同时给绝对值和百分比：

| Metric | Before | After | Change |
|---|---:|---:|---:|
| Total `Tensor.item()` time | `50.25s` | `0.36s` | `-99.3%` |
| Slow `Tensor.item() >50ms` | `18` | `0` | `-100.0%` |
| Max `Tensor.item()` | `209.153ms` | `10.174ms` | `-95.1%` |
| Input-prep p50 | `5.910ms` | `1.642ms` | `-72.2%` |
| Benchmark duration | `41.83s` | `40.20s` | `-3.9%` |
| Output tok/s | `72.54` | `75.47` | `+4.0%` |
| Mean TPOT | `15.93ms` | `15.25ms` | `-4.3%` |
| Mean ITL | `6.84ms` | `6.54ms` | `-4.4%` |

解释边界：

- 可以说：这个 PR 移除了 HunyuanImage3 AR embedding path 的一个逐 step GPU scalar sync，`Tensor.item()` profiler 总耗时下降 `99.3%`，同口径 no-profiler online benchmark 端到端吞吐提升约 `4%`。
- 不要说：这个 PR 解决了所有 GPU 空转。trace 仍显示 tail gap 集中在 `cudaGraphLaunch` / graph replay 提交边界。
- 不要用 profiler target request 的 TPOT 当最终性能结论；profiler run 只解释热点和调用栈。

精度结果不能只写一行 PASS。PR 里要写清楚：

- 为什么理论上不影响精度：所有 `<timestep>` token 仍然拿 `timestep_emb(0)`，非 `<timestep>` token embedding 不变。
- 为什么 AR-only accuracy 是相关检查：改动只在 AR embedding replacement，不碰 DiT image generation。
- 用什么输入：`tests/e2e/accuracy/test_hunyuan_image3.py` 里的同一组 `PROMPT` 和 `TEST_IMAGE_URLS`，prompt format 为 `task=it2i`、`bot_task=think_recaption`、`sys_type=en_unified`、`num_images=2`。
- 用什么指标：`text_prefix_match_count`，即输出 CoT 前缀与 reference CoT 连续相同的字符数。
- 结果：`text_prefix_match_count=29`，threshold `>=10`，PASS，AR output length `1181` chars。

如果 reviewer 要 “which benchmark scripts were used and paste corresponding results”，不要只回答 “vllm bench”。必须贴命令形态、server path、request payload、before/after 表、accuracy input/metric/result。

下次执行顺序：

1. 先跑纯 graph online path，确认 `vllm serve` ready 和 smoke 请求通过。
2. no-profiler benchmark 先给端到端数字。
3. request-window profiler 只用于解释热点：`start_profile -> target request -> stop_profile`。
4. trace 质量 gate 通过后再分析；文件小、进程少、缺 stack 时不能当正式 trace。
5. PR body 只写可复现证据，不写远端私有路径、IP、临时失败和垃圾测试。
