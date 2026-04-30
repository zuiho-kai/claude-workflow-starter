---
name: CI Hunyuan Perf Test Isolation
description: Hunyuan perf test 从 mandatory CI 拆出为独立 step，模型用 Instruct 变体，JSON 按配置拆分
type: project
originSessionId: e9b427d0-9d70-4f38-a8ed-3e53f47f593e
---
PR #2495 把 HunyuanImage3 perf test 从 mandatory "Diffusion X2I(&A&T) · Perf Test" 拆出。

**Why:** Hunyuan 80B MoE 在 CI 4×H100 上 dummy run OOM（原因：多个 parametrized test case 在同一 pytest session 里 server 没杀干净就起下一个，显存叠加爆了）。EXIT5 传播到 Qwen step 的 exit code，导致整个 mandatory step 失败。

**How to apply:**
- Hunyuan perf test 现在是独立 Buildkite step，`soft_fail: true` + `RUN_HUNYUAN_IMAGE3_PERF=1` env gate（默认不跑）
- 模型从 `tencent/HunyuanImage-3.0` 改为 `tencent/HunyuanImage-3.0-Instruct`（CI 节点 HF cache 里有 Instruct，没有 base，避免 30 分钟下载 + startup timeout）
- 原来一个 JSON（3 个 test case）拆成 3 个独立 JSON（tp4_fp8, tp2_fp8_sp2, tp2_fp8_cfgp2），每个 pytest 调用只起一个 server，防止显存残留
- profiling 脚本从 `scripts/profiling/` 移到 `tools/`，shell 脚本改为通用（model 作为 CLI 参数）
