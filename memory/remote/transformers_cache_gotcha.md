---
name: TRANSFORMERS_CACHE Overrides HF_HOME
description: 容器默认 TRANSFORMERS_CACHE 会覆盖 HF_HOME，必须 unset（空字符串不行）；OmniServer env_dict 只能覆盖不能删除环境变量
type: project
originSessionId: 4cc65e60-2b58-4a9f-9d4e-5bd1dffdc6b7
---
## TRANSFORMERS_CACHE 环境变量陷阱（2026-04-22 GEBench 调试发现）

容器默认 `TRANSFORMERS_CACHE=/models/huggingface/transformers`。transformers 库用 `cache_dir=os.environ.get("TRANSFORMERS_CACHE")` 传给 `hf_hub_download`，**覆盖** `HF_HOME` 推导的路径。

### 关键事实

1. `TRANSFORMERS_CACHE=`（空字符串）≠ `unset TRANSFORMERS_CACHE`
   - 空字符串：`os.environ.get("TRANSFORMERS_CACHE")` 返回 `""`，仍然传给 hf_hub_download
   - unset：返回 `None`，fallback 到 HF_HOME 路径

2. OmniServer 的 `_start_server()` 做 `env = os.environ.copy(); env.update(self.env_dict)`
   - 只能覆盖，不能删除变量
   - 如果容器有 TRANSFORMERS_CACHE，env_dict 无法 unset 它

### 解法

- bash 脚本：`unset TRANSFORMERS_CACHE`
- 单条命令：`env -u TRANSFORMERS_CACHE python ...`
- 验证：`python -c "import os; print('TRANSFORMERS_CACHE' in os.environ)"` → `False`

**Why:** transformers 库历史遗留设计，TRANSFORMERS_CACHE 优先级高于 HF_HOME。很多 Docker 镜像默认设了这个变量。

**How to apply:** 进容器后 `env | grep -i cache` 检查；run script 里永远加 `unset TRANSFORMERS_CACHE`；写 OmniServer env_dict 时意识到它不能删除变量。
