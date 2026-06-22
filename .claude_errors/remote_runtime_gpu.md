# Error Book: 远端运行时 / GPU / 依赖

## 2026-04-27 — Siglip2VisionModel 版本不兼容 (transformers 5.6.2)
**症状**：`AttributeError: 'Siglip2VisionModel' object has no attribute 'vision_model'`
**根因**：transformers 5.x 中 `Siglip2VisionModel` 自身就是 vision model，不再有嵌套 `.vision_model`
**解法**：`pipeline_hunyuan_image3.py:114` 去掉 `.vision_model` 后缀
**对未来的提醒**：transformers API 变化频繁，跑新环境先 `python -c "from transformers import X; print(dir(X(...)))"`

## 2026-05-18 — vLLM-Omni main 升到 vLLM 0.21 后只装 vllm 本体不够

**症状 1**：`upstream/main` 拉到 PR #3630 后，跑 HunyuanImage3 I2T 还没加载模型就 import 崩：
```text
ImportError: cannot import name 'split_routed_experts'
from vllm.model_executor.layers.fused_moe.routed_experts_capturer
```

**根因 1**：代码已经基于 vLLM 0.21 API，但远端现有 venv 仍是 vLLM 0.20.0 / 0.20.2；这些版本没有 `split_routed_experts`。

**解法 1**：在当前 worktree 建自己的 `.venv`，不要改共享 venv：
```bash
cd /tmp
uv venv --python /usr/bin/python3 --system-site-packages /home/wzr/wt-i2t-test-fix/.venv
uv pip install --python /home/wzr/wt-i2t-test-fix/.venv/bin/python --no-deps -U 'vllm==0.21.0'
```
然后验证：
```python
import importlib, vllm
m = importlib.import_module("vllm.model_executor.layers.fused_moe.routed_experts_capturer")
print(vllm.__version__, hasattr(m, "split_routed_experts"))
```

**症状 2**：只装 `vllm==0.21.0 --no-deps` 后，worker 初始化阶段崩：
```text
ImportError: cannot import name 'BatchDecodeWithPagedKVCacheWrapper' from 'flashinfer'
```

**根因 2**：`--system-site-packages` 让新 venv 捡到了系统路径里的残缺/旧 `flashinfer` namespace；而 `vllm==0.21.0` metadata 要求：
```text
flashinfer-python==0.6.8.post1
flashinfer-cubin==0.6.8.post1
```
只装 vLLM 本体不会补这些依赖。

**解法 2**：
```bash
cd /tmp
uv pip install --python /home/wzr/wt-i2t-test-fix/.venv/bin/python --torch-backend cu130 \
  'flashinfer-python==0.6.8.post1' 'flashinfer-cubin==0.6.8.post1'
```
安装后确认：
```python
import flashinfer
print(flashinfer.__version__, hasattr(flashinfer, "BatchDecodeWithPagedKVCacheWrapper"))
```

**注意**：这次 `uv pip install flashinfer...` 顺手把 `.venv` 里的 torch 拉到了 `2.12.0+cu130`，而 vLLM 0.21 metadata 要 `torch==2.11.0`，系统路径已经有 `2.11.0+cu130`。要卸掉 venv 内覆盖的 torch/triton，让它回落到系统 site-packages：
```bash
uv pip uninstall --python /home/wzr/wt-i2t-test-fix/.venv/bin/python torch torchaudio torchvision triton
```
再确认：
```text
torch 2.11.0+cu130
vllm 0.21.0
flashinfer-python 0.6.8.post1
```

**怎么避免**：
1. vLLM-Omni main import 新 vLLM symbol 失败时，先查 vLLM 版本和 symbol 是否存在，不要开始改源码：
   ```bash
   python - <<'PY'
   import importlib, vllm
   print(vllm.__version__)
   m = importlib.import_module("vllm.model_executor.layers.fused_moe.routed_experts_capturer")
   print(hasattr(m, "split_routed_experts"))
   PY
   ```
2. 用 `uv pip install --no-deps vllm==X` 后，必须查 `importlib.metadata.requires("vllm")` 里和 CUDA kernel 相关的 hard deps（flashinfer / torch / triton），逐项补齐或确认系统已有。
3. `--system-site-packages` 是为了复用大体积 torch/CUDA 包，但它也会暴露系统残缺 namespace。遇到奇怪 `ImportError: cannot import name ... from flashinfer (unknown location)`，先看 `flashinfer.__file__` 和 distribution version。
4. 用户明确说"新建 venv，把旧的干掉"时，只删除当前 worktree 自己的 `.venv`；删除前 `readlink -f` 确认路径在 worktree 内，绝不碰共享 `/home/wzr/vllm-omni/.venv`。

## 2026-05-18 — 跑 TP=2 要避开测试 helper 的全局 GPU cleanup/占卡假设

**症状**：用户要求 `tp=2 2,3卡`，但初次跑 pytest helper 仍等待 GPU 0/1/2/3 全部低于 5% 显存，且之前 0/1 上有别人的 TTS vLLM 服务；后来测试结束时 helper 还尝试清理它识别到的 `VLLM::StageEngineCoreProc`。

**根因**：测试 helper 的 GPU memory monitor / residual vLLM cleanup 是全局 0..N 视角，不知道当前 YAML 只用 devices `2,3`。Hunyuan stage config 控制运行设备，但 pytest fixture 的 pre/post cleanup 仍看整机。

**解法**：
- 按用户要求生成临时 YAML，把 `devices: "0,1,2,3"` 改成 `"2,3"`，`tensor_parallel_size: 4` 改成 `2`。
- 跑前用 `nvidia-smi --query-compute-apps` 和 `pgrep -af` 明确哪些进程是自己的，哪些是别人的服务。
- 如果 0/1 有他人服务，不要主动 kill；如果 helper 最后 kill 了残留，要在汇报里说明。

**怎么避免**：
1. 跑非全卡测试前，明确区分三层设备配置：YAML `runtime.devices`、`tensor_parallel_size`、pytest helper cleanup 的全局 GPU 视角。
2. 看到 pre-test monitor 等 0/1 卡，不要误判 TP=2 没生效；看 stage log：`Stage-0 set runtime devices: 2,3` 才是运行路径证据。
3. 多用户机器上，`pkill -f vllm` 这种全局命令禁用；只 kill 自己刚启动的 PID / stage proc。

## 2026-05-18 — GPU 占用判断只看 memory.used 漏了潜伏中的别人进程

**症状**：`nvidia-smi --query-gpu=memory.used` 全是 4 MiB，自信报"4 卡全空"，启动 HunyuanImage3 4 卡 deploy 之后 DiT 在 GPU 2,3 OOM；查 compute-apps 才发现别人有 `end2end.py text2img` 已经 spawn 但 model 还没完全 load（瞬时只占几 MB）。前后浪费 ~5 分钟用户问"我看没人跑"才回头复查。

**根因**：`memory.used` 是 PyTorch reservation 的瞬时值，进程启动到 model load 之间有几十秒 GPU 几乎空。判断 GPU 是否"我的"必须同时看：
- `nvidia-smi --query-gpu=memory.used` —— 当下已分配
- `nvidia-smi --query-compute-apps=pid,process_name,gpu_uuid,used_memory` —— 已注册到 driver 的进程
- `ps -ef | grep -E "(hunyuan|end2end|vllm|VLLM::)"` —— 包括刚 spawn 还没 attach kernel 的 python 进程

**解法**：跑前三件套并行查；用 `nvidia-smi --query-gpu=index,uuid` + compute-apps 的 gpu_uuid 列做映射，确认哪个物理 GPU 是哪个 worker 的。

**怎么避免**：
1. 远端跑 GPU job 前必跑"三件套"：`memory.used` + `compute-apps` + `ps -ef | grep python`，缺一不可。
2. 不要在用户说"全空"之后跳过自查。用户可能基于上一刻看到的状态，跟你眼下抢卡的窗口不重叠。
3. 三件套写成脚本，会话开头跑一次：`bash gpu_owner_check.sh`，输出三类一起看。

## 2026-05-18 — 端到端 smoke 撞 vllm scheduler API 漂移，单测能过但真跑崩

**症状**：本次 PR (#3626 HunyuanImage3 infer_align_image_size) 单测在 `wt-i2t-test-fix/.venv` (vllm 0.21.0) 全过，真跑 `end2end.py img2img` 时 `OmniARAsyncScheduler` 调 `self._get_routed_experts(request)` AttributeError 立刻 die。换 `vllm-omni-pr3444-online-prompt-align/.venv` (vllm 0.20.2) → DiT forward 时 flashinfer ninja JIT `fused_moe_90` 失败。

**根因**：
- 仓库 HEAD 写的代码暗中假设了 upstream vllm 的某个版本（`_get_routed_experts` 是 0.20.x 的；0.21.0 不存在）。
- "单测过"覆盖的只是被改动的 hot path（mm_processor / sampler / postprocess），不会触碰 scheduler + DiT forward。
- venv 是别的 PR 留下来的，没人保证跟你 PR 的 vllm 期望一致。

**解法**：
1. rebase 到主干（main 当前已对齐 vllm 0.21.0），仓库代码、venv、upstream 三方对齐后端到端通。
2. 真正修复路径不是改 venv 也不是 stub 接口，是 git rebase origin/main。

**怎么避免**：
1. **venv 健康检查脚本**：选 venv 前先跑
   ```bash
   $venv/bin/python -c "
   import vllm; print('vllm:', vllm.__version__)
   from vllm.v1.core.sched.scheduler import Scheduler
   print('_get_routed_experts:', hasattr(Scheduler, '_get_routed_experts'))
   import flashinfer; print('flashinfer:', flashinfer.__version__)
   "
   ```
   把"仓库 HEAD 期望调用的 upstream symbol"逐项 hasattr 一遍，3 秒钟决定 venv 配不配。
2. **单测过 ≠ 真跑过**：单测只覆盖 mm_processor / postprocess 这类窄路径；scheduler + forward + KV transfer + connector 整链路必须真跑一次。声明 PR "已验证"前必须有 end-to-end 真跑证据。
3. **PR 长时间未 rebase + main 升了 vllm 大版本**：先 `git rev-list --count main..HEAD --left-right` 看 behind 数；behind ≥ 20 且涉及 vllm 主版本变化时，先 rebase 再调试，别拿旧 venv 硬试。
4. PR 描述里要标注"在 vllm X.Y.Z 上验证过"；reviewer 看到 vllm 版本不匹配可以直接打回。
