# Error Book: Profiling & 模型加载

## 2026-04-23 — 没做侦察 + judge 模型未预下载
**症状**：跑了 4 小时才跑通；judge 报 `LocalEntryNotFoundError`
**根因**：没做侦察 + `HF_HUB_OFFLINE=1` 下 judge 模型遗漏
**提醒**：accuracy test 涉及 generate + judge 两个模型，都要预下载

## 2026-04-23 — 连续跑多配置时 GPU 显存残留 OOM
**症状**：tp4_fp8 跑完立即跑 tp2_sp2，OOM
**根因**：进程退出后 GPU 显存未立即释放
**解法**：每轮之间 `pkill -9 && sleep 5 && nvidia-smi` 确认归零

## 2026-04-27 — HF_HUB_CACHE 覆盖 HF_HOME 导致 server 600s 超时
**症状**：server 启动后 GPU 全程 0 MiB，600s 超时，模型从未加载
**根因**：Docker 镜像设了 `HF_HUB_CACHE=/models/hub`，优先级高于 `HF_HOME=/home/models`
**解法**：进容器后 `unset HF_HUB_CACHE`
**提醒**：`HF_HUB_CACHE` 和 `TRANSFORMERS_CACHE` 都要 unset，不能只 unset 一个

## 2026-04-27 — async_chunk=True 默认值导致 HunyuanImage3 启动 ValueError
**症状**：`ValueError: Pipeline 'hunyuan_image_3_moe' has async_chunk=True in deploy but no stage declares a next-stage input processor`
**根因**：`DeployConfig.async_chunk` 默认 `True`；HunyuanImage3 没有 deploy YAML；DIT_ONLY 单阶段 pipeline 没有 next-stage processor
**解法**：创建 `vllm_omni/deploy/hunyuan_image_3_moe.yaml`（`async_chunk: false`），或加 `--no-async-chunk`
**提醒**：单阶段 diffusion 模型没有 deploy YAML 时必须加 `--no-async-chunk`

## 2026-04-27 — Siglip2VisionModel 版本不兼容 (transformers 5.6.2)
**症状**：`AttributeError: 'Siglip2VisionModel' object has no attribute 'vision_model'`
**根因**：transformers 5.x 中 `Siglip2VisionModel` 不再有嵌套 `.vision_model` 属性
**解法**：远端 `pipeline_hunyuan_image3.py:114` 去掉 `.vision_model` 后缀
**提醒**：新环境先验证核心模块 API：`python -c "from X import Y; print(dir(Y(...)))"`

## 2026-04-27 — HF 官方 pipeline 无法在 L20X 云实例上跑通
**症状**：`AutoModelForCausalLM.from_pretrained` 加载成功，但 `generate_image()` 时 `HunyuanStaticCache` 报 `AttributeError: 'HunyuanStaticCache' object has no attribute 'layers'`
**根因**：模型仓库的 `trust_remote_code` Python 文件引用了 transformers 新版 `StaticCache` API（有 `layers` 属性），但 transformers 4.50 的 `StaticCache` 没有该属性；升级 transformers 则 `lazy_initialization()` 签名不匹配
**尝试**：
- transformers 5.6.2 → `StaticLayer.lazy_initialization() missing 1 required positional argument`
- transformers 4.50.0 → `HunyuanStaticCache has no attribute 'layers'`
- 清除 `~/.cache/huggingface/modules/` + `HF_HUB_OFFLINE=1` → 同样报错
**结论**：模型仓库代码处于版本夹缝中，需要找到精确匹配的 transformers 版本（可能 ~4.52-5.0）或 pin 模型仓库 commit revision
**对未来的提醒**：跑 HF 官方 baseline 前先确认 transformers 版本兼容范围，用 `--revision` pin 到已知可用的 commit

## 2026-04-28 — trust_remote_code 模型的 patch 被反复覆盖
**症状**：patch 了 `modeling_hunyuan_image_3.py` 的 SDPA attn_mask dtype，重跑后 patch 消失，报同样的错
**根因**：`trust_remote_code=True` 加载时，transformers 从 snapshot 目录重新复制 `.py` 文件到 `~/.cache/huggingface/modules/transformers_modules/`，覆盖之前的 patch
**解法**：必须**同时 patch 两个位置**的文件：
  - `/mnt/models/hub/models--xxx/snapshots/<hash>/modeling_hunyuan_image_3.py`（源）
  - `/mnt/models/modules/transformers_modules/<hash>/modeling_hunyuan_image_3.py`（缓存）
  - 并且设 `HF_HUB_OFFLINE=1` 防止从 HF Hub 重新下载
**对未来的提醒**：trust_remote_code 模型的代码有三层缓存（HF Hub → snapshot → modules），patch 必须覆盖源头

## 2026-04-28 — attn_implementation="eager" 对自定义 attention dispatch 无效
**症状**：传了 `attn_implementation="eager"` 但模型仍然走 SDPA，报 `key.size(1) != value.size(1)`
**根因**：模型自定义了 `Hunyuan_ATTENTION_CLASSES` dict（line 1375），硬编码只有 `HunyuanImage3SDPAAttention`，完全忽略 `from_pretrained` 的 `attn_implementation` 参数
**解法**：需要在 `Hunyuan_ATTENTION_CLASSES` 里加一个 eager 实现（用 `torch.matmul` + `softmax` 替代 `scaled_dot_product_attention`），或直接 patch `HunyuanImage3SDPAAttention.forward` 把 SDPA 换成手动实现
**对未来的提醒**：`trust_remote_code` 模型的 `attn_implementation` 参数不一定生效——先 `grep ATTENTION_CLASSES` 看模型自己的 dispatch 逻辑

## 2026-04-28 — pip install torchvision 把 torch 升级到不兼容版本
**症状**：`RuntimeError: The NVIDIA driver on your system is too old (found version 12080)`
**根因**：`pip install torchvision`（不 pin 版本）拉了最新 torchvision，连带把 torch 从 2.7.0 升到 2.11.0（需要 CUDA 13），和 12.8 驱动不兼容
**解法**：安装时必须同时 pin torch 和 torchvision 版本：`pip install torch==2.8.0 torchvision==0.23.0`
**对未来的提醒**：永远不要单独 `pip install torchvision`，必须和 torch 一起 pin 版本

## 2026-04-28 — 用户要 torch profiler trace，给了 benchmark stats JSON
**症状**：用户说"我要的是每个算子的细节，我要那种可以时序图的json"
**根因**：只跑了 `run_diffusion_profiling.sh` 的 Phase 1（stage_durations benchmark），没跑 Phase 2（torch profiler trace）
**解法**：用 `--profiler-config` 参数启动 server，发请求后 `/start_profile` + `/stop_profile` 收集 `trace_rank*.json.gz`
**对未来的提醒**：profiling 有两种产物——benchmark stats（吞吐/延迟/stage duration）和 torch trace（算子级时序图），确认用户要哪种

## 2026-04-28 — HF 模型 RoPE 广播导致 SDPA key/value size 不匹配
**症状**：`RuntimeError: Expected key.size(1) == value.size(1) to be true, but got false`，发生在 AR decode 阶段的 CFG unconditional 路径
**根因**：`apply_rotary_pos_emb` 在 `position_ids=None` 时，cos/sin shape `[1, max_pos_emb, head_dim]` 通过广播把 key 从 `[1,32,1,128]` 扩到 `[1,32,22800,128]`，但 value 没过 RoPE 保持 `[1,32,1,128]`
**解法**：在 `apply_rotary_pos_emb` 里加截断：`position_ids is None` 时 `cos = cos[..., :q.size(-2), :]`
**对未来的提醒**：RoPE 函数里 cos/sin 和 q/k 的 seq_len 维度必须对齐，广播会静默扩张 tensor

## 2026-04-28 — HF 模型 CFG 2D attention_mask 传给 SDPA 报错
**症状**：修完 RoPE 后新报错 `The expanded size of the tensor (1) must match the existing size (2) at non-singleton dimension 3`
**根因**：transformers 4.57.1 的 `UnbatchedClassifierFreeGuidanceLogitsProcessor.get_unconditional_logits()` 传 2D `[1, N]` padding mask 给模型 forward，SDPA 期望 4D `[B, 1, Q, K]` mask
**解法**：在 SDPA 调用前加 guard：`if attention_mask is not None and attention_mask.ndim == 2: attention_mask = None`
**对未来的提醒**：CFG unconditional 路径的 attention_mask 格式和正常路径不同，SDPA attention 需要做 ndim 检查

## 2026-04-28 — torch.profiler 包整个 generate_image() → 23GB+ trace 爆炸
**症状**：profiler 导出 trace 时 RSS 涨到 250GB，trace 文件 23GB+，chrome://tracing 打不开
**根因**：`with profile(...): model.generate_image(...)` 把 AR prefill（1234 tokens × 33 layers × MoE）+ AR decode + diffusion 全录进去了。80B 模型即使只跑 13s，kernel 调用量也是百万级
**解法**：monkey-patch pipeline 的 `progress_bar` context manager，在 `__enter__` 里 `prof.__enter__()`，`__exit__` 里 `prof.__exit__()`，精确只包 denoising loop → 1.2GB trace（79MB gz）
**对未来的提醒**：大模型 profiling 必须精确控制 profiler 范围。不要包整个推理流程，只包目标阶段（如 denoising loop）。用 monkey-patch 注入 profiler 比改源码更灵活

## 2026-04-28 — diff_infer_steps 参数不是 generate_image 的 kwarg
**症状**：`generate_image(diff_infer_steps=10)` 传了但模型跑了 50 步（默认值）
**根因**：`diff_infer_steps` 是 `generation_config` 的属性，不是 `generate_image` 的 kwarg。pipeline 从 `gen_config.diff_infer_steps` 读取
**解法**：`model.generation_config.diff_infer_steps = 10`
**对未来的提醒**：HF 模型的 diffusion 参数在 `generation_config` 里，不在 `generate_image` kwargs 里

## 2026-04-28 — vllm-omni profiler delay_iterations:1 + 单请求 → 空 trace
**症状**：trace 文件只有 21-25KB，profiler_out 只有 2 个调用（cudaDeviceSynchronize + Activity Buffer Request）
**根因**：profiler config `delay_iterations:1` 跳过第一个 step()，但只发了 1 个请求，所以 profiler 跳过了唯一的请求
**解法**：`delay_iterations:0`，让 profiler 立即开始录制 → 47MB/rank trace
**对未来的提醒**：单请求 profiling 时 `delay_iterations` 必须为 0

## 2026-04-28 — pkill -f python 杀死 SSH session
**症状**：`ssh ... "pkill -9 -f python; ..."` 执行后 SSH 断开，exit code 255
**根因**：`pkill -f python` 匹配所有含 "python" 的进程，包括 SSH session 的子进程
**解法**：用精确 PID kill（`ps aux | grep bench_hf | awk '{print $2}' | xargs kill -9`），或用更精确的 pattern（`pkill -f bench_hf_trace`）
**对未来的提醒**：远端 `pkill -f` 永远不要用 `python` 这种宽泛 pattern，用具体脚本名

## 2026-04-28 — monkey-patch F.scaled_dot_product_attention 没生效
**症状**：替换了 `torch.nn.functional.scaled_dot_product_attention`，但模型代码里的诊断 print 没出现
**根因**：模型文件用 `import torch.nn.functional as F` 后直接调 `torch.nn.functional.scaled_dot_product_attention(...)`，monkey-patch `F.scaled_dot_product_attention` 不影响已绑定的引用
**解法**：直接 patch 模型源文件（snapshot + cache 两个位置），加 print 语句
**对未来的提醒**：monkey-patch 标准库函数对 `trust_remote_code` 模型不可靠，直接改源文件更稳

## 2026-04-28 — patch 了错误的 cache 路径
**症状**：patch 了 `/mnt/models/modules/transformers_modules/...` 但模型实际加载的是 `/root/.cache/huggingface/modules/transformers_modules/...`
**根因**：不同环境下 transformers modules cache 路径不同，取决于 `HF_HOME` / `TRANSFORMERS_CACHE` / 默认值
**解法**：看 traceback 里的实际文件路径，patch 那个路径。同时 patch snapshot 源文件防止被覆盖
**对未来的提醒**：先跑一次看 traceback 确认实际加载路径，再 patch

## 2026-06-17 — LTX2.3 开图 profiling 把 eager trace 和 graph benchmark 混成一个结论
**症状**：用户要求看 LTX2.3 T2V 开图后的气泡和算子耗时。我先用已有 eager torch trace 分析了“气泡很多”，同时引用了开图 e2e benchmark 结果，导致表达上像是在分析开图 trace。用户追问后才确认本地和远端当时都没有可用的开图 `trace_rank*.json(.gz)`；已有完整 trace 来自 `/data/wzr/ltx23_t2v_offline_trace_20260616_142741`，脚本明确带 `--enforce-eager`。

**根因**：
- 没有先做 profiling artifact gate：没有逐项确认 trace 文件、run script、server log、`--enforce-eager` / `transformer compiled with torch.compile` 属于同一轮。
- 把两个证据层混用：无 profiler steady benchmark 只能证明 e2e / qps，torch trace 才能证明算子和气泡。
- 补跑时一开始没有复用已成功的 serving `/v1/videos/sync` benchmark 路径，而是写了 direct `Omni(...)` runner，worker 初始化 EOF，扩大了变量面。
- 远端脚本 cleanup 只杀外层 PGID，没有复查实际 server PGID，导致 profiler server 进程残留，需要按本轮 PID/PGID 精确清理。

**解法**：
1. 先枚举远端所有 `trace_rank*.json(.gz)`，再读对应 `run*.sh` / `server.log`，确认没有现成开图 trace。
2. 复用已经跑通的 serving benchmark 路径，只加 `--profiler-config` 和 online `/start_profile -> /v1/videos/sync -> /stop_profile`。
3. 用 full-shape warmup 丢弃 cold compile/capture，再 profile 真实 512x384、25 frames、20 steps 请求。
4. 交付前确认三类证据同轮一致：`transformer compiled with torch.compile`、`profiled_request.json` 成功、`trace_rank0.json.gz` 落盘并下载/解压。
5. 清理时按实际 server PID/PGID 精确 kill，并复查 `nvidia-smi`，不能只依赖外层 shell PGID。

**对未来的提醒**：
- 用户说“开图后的气泡 / 算子耗时”时，必须先证明 trace 是 graph mode：无 `--enforce-eager`，日志有 `Model runner: transformer compiled with torch.compile`，trace 文件属于同一 run。
- e2e/qps 和 profiler trace 必须分开汇报：e2e 用无 profiler steady benchmark；气泡/算子用 profiler 单请求 trace，并注明 profiler overhead。
- 已有成功 benchmark 路径时，只做最小增量加 profiler，不换 runner、不重写入口。
- 如果只有 benchmark stats 没有 trace，要直接说“当前没有 trace profiling artifact”，不能拿 benchmark 或其他模式 trace 补位。

## 2026-06-17 — LTX2.3 mask-sync 优化看似减同步但会改精度
**症状**：为减少 graph mode 下 prompt attention mask 的 `torch.any(~attention_mask)`、`_get_unpad_data()`、`.item()` 等重复同步，尝试在 LTX2.3 T2V 中提前把 `encoder_attention_mask` 包装成 `AttentionMetadata` 并传给 FlashAttention。单元测试能证明部分 mask 形状和值正确，但真实 LTX2.3 graph accuracy 失败：mask-sync candidate 的 PPM similarity 只有 SSIM `0.9338` / `0.9340`，低于 `0.94` 阈值。dtype-only 对照在同一 head `f19a26dd1448430346c5f31e9973ef6579895bbd` 上通过，SSIM `0.9634`、PSNR `36.67`，所以精度退化来自 mask-sync 实验，不是 dtype 前置 cast。

**根因**：
- 第一个实现直接从 pipeline/transformer 顶层构造 `AttentionMetadata`，绕过了 LTX2.3 原来的 `2D mask -> additive bias -> attn.prepare_attention_mask -> head view -> _to_padding_mask` 路径。原始 float `0/1` mask 如果直接走 `_to_padding_mask`，`0 >= 0` 会被当成 valid，padding 语义会错。
- 第二个实现改成 additive mask 后再构造 metadata，但仍提前绕过每层 processor 的 mask prepare/shape path；真实 accuracy 仍失败，说明 LTX2.3 prompt mask 不能只靠“看起来等价的 2D padding mask”替代原路径。
- 预计算 `_upad_input` 的 indices/cu_seqlens 不是唯一问题；即使只缓存 dense/has-padding 判断、不复用 unpad data，也会掉精度。

**已验证证据**：
- dtype-only PR 分支：`/data/wzr/wt-ltx23-t2v-graph-opt-pr4464-dtype`，run `/data/wzr/ltx23_dtype_only_pr4464_accuracy_candidate_20260617_170834`，`passes_thresholds=true`。
- mask-sync full metadata candidate：`/data/wzr/ltx23_mask_sync_pr4464_accuracy_candidate_20260617_170042`，SSIM `0.9337558`，失败。
- mask-sync dense-only candidate：`/data/wzr/ltx23_mask_sync_pr4464_accuracy_candidate_20260617_171809`，SSIM `0.9337558`，失败。
- mask-sync after `attn.prepare_attention_mask` candidate：`/data/wzr/ltx23_mask_sync_pr4464_accuracy_candidate_20260617_172652`，SSIM `0.9340195`，失败。

**遗留问题 / 禁止重复踩坑**：
- 不要再从 LTX2.3 pipeline 或 transformer 顶层直接用 prompt mask 构造 `AttentionMetadata` 来替代 processor mask path，除非先做逐层对齐：baseline 与 candidate 的 `attention_mask` shape/value、backend branch、FlashAttention call 输入必须逐项一致。
- mask 同步优化下一步只能在不改变原 mask path 的地方做，例如 backend 内部只优化 dense no-mask fast path、或在 processor 内缓存完全等价的 prepared mask，并先通过带 padding prompt 的 LTX2.3 graph accuracy。
- 任何“mask 优化很快”的性能数字，在 accuracy 通过前都只能叫 invalid candidate，不能进入 PR、benchmark 表或对外结论。
