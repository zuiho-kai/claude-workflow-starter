# Painterly bug — 调查方法上的踩坑

painterly 调查过程中**调查方法本身**反复犯的错。根因和总览见 [`painterly_root_cause.md`](painterly_root_cause.md)。

---

## 2026-05-05 16:30 — 主观对图先于 grep 日志，导致 "FA3 是 bug" 误判

**症状**：用 `DIFFUSION_ATTENTION_BACKEND=TORCH_SDPA` env override 后跑出来的图，跟之前 baseline run（理论 FA3）"看起来"猫更卡通，于是宣告"FA3 是 painterly 的主要源头"。

**根因**：`vllm_omni/diffusion/models/hunyuan_image3/pipeline_hunyuan_image3.py:341` 在 pipeline `__init__` 里硬编码 `os.environ["DIFFUSION_ATTENTION_BACKEND"] = "TORCH_SDPA"`，**HunyuanImage3 永远走 SDPA**，FA3 从来没被调过。两次 run 都是 SDPA，肉眼差别只是 NCCL all-reduce 顺序、worker 启动时间引入的 RNG 抖动。

**解法**：定位 attention backend 必须先 `grep "diffusion attention backend" /tmp/<run>.log`，看实际写到日志的字符串，再下结论。

**对未来的提醒**：
- 别用主观对图作为单一证据下结论。两次 run 的图就算同 seed，TP/NCCL 顺序差也会让小细节跳
- 走代码路径前，先在日志里搜真正被调的实现名（"Using XXX backend"、"FlashAttention"、"sdpa"）
- 如果看到怀疑的 baseline 改动让图变好/变坏，先用 `head -200 /tmp/<run>.log` 找配置 echo，确认改动真的生效

---

## 2026-05-05 16:00 — SigLIP2 输出 std=0.06 看起来"坍缩"，没核对 HF 参考就跳到 root cause

**症状**：dump 出 `vit_raw` 看到 1119/1152 channel 跨 patches 的 std<0.01、overall std=0.06、token-token diff=0.0036，下意识判定 "SigLIP2 vision tower 坍缩，空间信息全丢，这就是 painterly 根因"。

**根因**：std=0.06 是 SigLIP2 **post_layernorm 的设计行为**，HF bundled `siglip2.Siglip2VisionTransformer`（HunyuanImage3 训练时用的同一份代码）跑出来 std=0.06015、diff vs transformers 5.x 仅 mean=0.00003。两个实现数值等价，HF 参考也接受 std=0.06 conditioning 然后 DiT 能生成正常卡通——所以这个 std 不是 bug。

**解法**：在标"SigLIP2 坍缩"为 root cause 之前，必须用同一份输入 + 同一份 weights 跑一次 HF 实现/官方 demo 对照，确认对方不是同样 std。`probe_hf_bundled_siglip.py` 模式：5 分钟独立 python 脚本，2 个实现 forward 一遍，print stats + diff。

**对未来的提醒**：
- "看起来不对" 的统计指标（坍缩、爆炸、零值）必须有 baseline 对照才算证据。HF 官方 demo / training-time bundled code 是首选 baseline
- 模型设计本身可能有反直觉行为（attention sink token、outlier channel、post-LN 把跨 token 信息洗掉……）。"std 异常小" ≠ bug
- "通过对比验证假设" 这个 step 要在 1 小时内做完，不要先写一堆 dump probe 然后才回头验证 baseline

---

## 2026-05-05 16:50 — 尝试 swap SigLIP2 实现时连续踩 3 个接口错

**症状**：把 `transformers.Siglip2VisionModel` swap 成本地 `vllm_omni.model_executor.models.hunyuan_image3.siglip2.Siglip2VisionTransformer`，依次撞上：
1. `'Siglip2VisionConfig' object has no attribute 'items'` — 本地版 `Config(config)` 包装期望 dict
2. `name 'extras' is not defined` — 之前 COT dump patch 时 anchor 串错改坏了变量名
3. `'Config' object has no attribute 'use_return_dict'` — 本地版 forward 期望 `return_dict` 显式传入或 config 里有该 key

**根因**：本地 SigLIP2 是从 HF snapshot **逐字 vendor**（`/mnt/models/.../siglip2.py`）来的，**不是** `transformers.Siglip2VisionModel` 的 drop-in replacement。两者构造签名、forward 签名、config 接口、kwarg 命名全有差异。我没先把这些差异列清楚就动手 patch + 跑，每跑一次撞一个错。

**解法**：swap 不同实现前，先生成"接口 diff 矩阵"——把两侧的 `__init__` 签名、`forward` 签名、config 期望字段、return type 全列出来对比，再写 adapter shim 把所有差异在一处 reconcile，最后才 sed。

**对未来的提醒**：
- 当 commit 上写"swap A → B 因为它们等价" 时，"等价" 通常只指**数值**等价，**接口**几乎从来不等价。先审接口
- "vendor 一份 HF 上游代码" 类型的 swap 容易踩这种坑：vendor 版本用了已 deprecated 的 API（这里是 `_prepare_4d_attention_mask`，transformers 5.10 要删）、没跟上签名 rename（`attention_mask` vs `pixel_attention_mask`）
- 用户 push 回 "再犯错就从头审视，不要老是改出小问题再修" 之后，立刻停手做完整接口对账，**不要再迭代式修补**

---

## 2026-05-05 17:00 — 远端代码累积多个改变行为的 patch 没回退，影响后续诊断

**症状**：调研中陆续 patch 了 `VAE decode FP16→BF16`、`VAE encode FP16→BF16`、`disable autocasts`、`force MATH SDPA`、`swap to local SigLIP2` ……失败的实验回退了，成功+无影响的实验留下 dump probe，但 **"实验性的精度改动"（BF16/FP16 swap）忘记 revert**。后面跑诊断时分不清当前 baseline 是 vanilla cr/pr3107-fix 还是带了 4 个隐式改动的混合态。

**根因**：缺少 patch ledger。每次 patch 写一个 `.sh` 脚本到 `/tmp/patch_*.sh`，但没维护"当前活跃 patch 列表"，靠肉眼追踪。

**解法**：每次启动新调研 session 先 `grep -rn "BUG-PROBE\|VLLM_OMNI_DUMP\|_OmniSigl" /rebase/vllm-omni/` 全量审计当前所有改动；把改变行为的 patch 跟纯 dump probe 区分清楚，前者要求 explicit toggle（env var 或最小改动），不能默认 enabled。

**对未来的提醒**：
- 远端 patch session 开头和切换大假设之前，**强制审计当前 patch 状态**。`grep "BUG-PROBE"` 是廉价 check
- 探针 patch（dump、log）和实验 patch（改 dtype/kernel/algo）应该用不同的 marker。比如 dump 用 `BUG-PROBE`，实验改动用 `EXPERIMENT-PATCH`，方便选择性 grep + revert
- 用 env var gate 一切实验性数值改动，不要直接改默认值——这样 baseline 跟 vanilla 一致，experiment 跟 baseline 在同一份代码里 toggle

---

## 2026-05-05 18:30 — 一次翻 5 个 cuDNN/CUBLAS 旋钮 + CUBLAS_WORKSPACE_CONFIG，把容器跑崩

**症状**：为了试 cuDNN 9 / TF32 / autotuning 是不是 painterly 来源，在 `vllm_omni/__init__.py` 加了 env-gated 一次性翻 5 个旋钮：
```python
cudnn.deterministic = True
cudnn.benchmark = False
cuda.matmul.allow_tf32 = False
cudnn.allow_tf32 = False
set_float32_matmul_precision('highest')
```
配 `CUBLAS_WORKSPACE_CONFIG=:4096:8` 一起跑 IT2I。后台启动 + sleep 200s 期间，远端 docker exec 报 `OCI runtime exec failed: exec failed: unable to start container process`，**整个容器死了**，SSH `Connection refused`，用户被迫重新申请容器。

**根因**：`cudnn.deterministic=True` + `CUBLAS_WORKSPACE_CONFIG=:4096:8` 强制 PyTorch 走 deterministic 算法。HunyuanImage3 DiT 用了 Conv3d / 某些 attention kernel 在 cuDNN 9 / CUDA 13 下**没有 deterministic 实现**，runtime 抛 CUDA error → worker 进程崩 → 容器 OOM 或 segfault → 整个 docker 死。

**解法**：调试性"flip stability knobs"必须**分级单步**翻，每加一个就跑一次 sanity check：
- L1（最不侵入）：只 `cudnn.allow_tf32=False` + `cuda.matmul.allow_tf32=False` —— 关 TF32 走 FP32，几乎不会 crash，只是慢一点
- L2：+ `cudnn.benchmark=False` —— 关 autotuning，picks 默认 kernel
- L3：+ `set_float32_matmul_precision('highest')` —— 等价 L1 但用新 API
- **永远不加** `cudnn.deterministic=True` 和 `CUBLAS_WORKSPACE_CONFIG=:N:N`，除非确认每个 op 都有 deterministic 实现

每个旋钮 init 用 `try/except` 包裹，失败不影响后续 import。

**对未来的提醒**：
- "为快速 disambiguate 一锅端"看似省时，实际只要其中一个 flag 引发 runtime error 就连带把所有其他 flag 的实验数据废掉，反而最慢
- 对硬件级旋钮（cuDNN/CUBLAS/NCCL）下手前先 grep 是否有 known-failure 的 op：HunyuanImage3 用 Conv3d，cuDNN 9 deterministic Conv3d 实现长期 buggy，是 known landmine
- 容器死掉的代价高（用户重申请、所有 /tmp 数据丢失），比"实验慢"严重得多
