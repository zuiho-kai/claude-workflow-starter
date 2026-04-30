---
name: HF trust_remote_code 模型调试教训
description: 2026-04-28 HunyuanImage3 HF baseline profiling 连续失败的行为反思，避免重复犯错
type: feedback
---

## 1. 先读官方 requirements.txt，不要猜版本
transformers 4.50 → 5.6.2 → 4.57.1 试了三轮才发现官方 requirements.txt 写的是 4.57.1。浪费 40+ 分钟。
**Why:** 每次装错版本 = 重建 venv + 重新加载模型（各 5 分钟），三轮就是 30 分钟。
**How to apply:** 跑任何 HF 模型的官方 demo 前，第一步 `curl` 他们的 `requirements.txt`，用精确版本。

## 2. trust_remote_code 模型不要假设标准参数生效
`attn_implementation="eager"` 传了但模型自定义了 `Hunyuan_ATTENTION_CLASSES` 硬编码只有 SDPA。试了 3 轮 eager 都没用。
**Why:** trust_remote_code 的模型代码完全自治，可以忽略任何 from_pretrained 参数。
**How to apply:** 第一次报错就 `grep ATTENTION_CLASSES` 或 `grep attn_impl` 看模型自己的 dispatch，不要反复换参数。

## 3. 第一次失败后查根因，不要换参数重试循环
transformers 版本换了 3 次，attn_implementation 换了 2 次，patch 了 4 次。每次都是"换个参数再试"而不是"看代码理解为什么失败"。
**Why:** 盲试 N 次的期望收益远低于花 5 分钟读代码找根因。
**How to apply:** 远端报错后，先 `sed -n` 看报错行附近 20 行代码，理解逻辑再决定修法。最多试 2 次，第 3 次必须读代码。

## 4. 确认用户要什么产物再跑
用户要 torch profiler trace（时序图 JSON），我跑了 benchmark stats JSON。浪费一轮完整的 3 配置 benchmark 时间。
**Why:** profiling 有两种产物，不确认就跑 = 50% 概率白跑。
**How to apply:** 用户说"profiling"时，问清楚要 benchmark stats 还是 torch trace（chrome://tracing）。

## 5. pip install 单个包会拉升整个依赖链
`pip install torchvision` 把 torch 从 2.7 升到 2.11，CUDA 不兼容。
**Why:** pip 的依赖解析会升级已安装的包。
**How to apply:** 永远同时 pin torch + torchvision + torchaudio 版本，或用 `--no-deps`。

## 6. trust_remote_code 模型 patch 必须改 snapshot，不能改 cache（2026-04-29 新增）
`from_pretrained(..., trust_remote_code=True)` 每次启动都从 snapshot 重新复制到
`$HF_HOME/modules/transformers_modules/<hash>/`，覆盖对 cache dir 的任何手动 patch。
**Why:** transformers 的 `dynamic_module_utils` 每次调用都做 hash 校验并重建 cache。
**How to apply:** 改 snapshot 文件（`hub/models--xxx/snapshots/<hash>/模型文件.py`），
不要改 `modules/transformers_modules/` 下的文件；patch 完后 `rm -rf modules/transformers_modules/<hash>/` 强制重建。

## 7. 有 runbook 就直接用 runbook 的版本，任何"先试别的"都是浪费（2026-04-29 新增）
本次会话用了 transformers 5.6.2 打了 7+ 个补丁（lazy_initialization / use_cache / KeyError），
全部是因为没用 runbook 指定的 4.57.1。正确做法：看 runbook → 找指定 venv → 直接跑。
**Why:** 官方指定版本是已验证过的，跑过的。偏离一个版本 = 引入任意多个 API 变化。
**How to apply:** 进远端第一步 `grep transformers requirements.txt`，对上了再跑。
`venv_hf` = transformers 4.57.1（HF baseline 专用）；`venv` = transformers 5.6.2（vllm-omni 专用）。
