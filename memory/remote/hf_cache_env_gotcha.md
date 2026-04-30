---
name: HF cache 环境变量陷阱（TRANSFORMERS_CACHE / HF_HUB_CACHE 都覆盖 HF_HOME）
description: 容器默认设的 TRANSFORMERS_CACHE 和 HF_HUB_CACHE 优先级都高于 HF_HOME，必须 unset（空字符串 ≠ unset）；OmniServer env_dict 只能覆盖不能删除变量
type: rule
---

## 核心事实

容器镜像可能同时设了 `TRANSFORMERS_CACHE` 和 `HF_HUB_CACHE`，**两者优先级都高于** `HF_HOME`。只 unset 一个不够。

- `os.environ.get("TRANSFORMERS_CACHE")` 返回的值会被 transformers 直接传给 `hf_hub_download`，覆盖 `HF_HOME` 推导路径
- `HF_HUB_CACHE` 同理（huggingface_hub 库直接读）
- **空字符串 ≠ unset**：`TRANSFORMERS_CACHE=""` 仍被 `os.environ.get` 返回 `""`，行为不可预测；`unset` 才返回 `None`

## 进容器必做

```bash
# 检查所有 cache/HF 相关变量
env | grep -iE "cache|hf_home|offline"

# 一律 unset，再设 HF_HOME
unset TRANSFORMERS_CACHE
unset HF_HUB_CACHE
export HF_HOME=/home/models   # 或节点对应的持久挂载路径

# 验证
python -c "import os; print('TRANSFORMERS_CACHE' in os.environ, 'HF_HUB_CACHE' in os.environ)"
# 期望：False False
```

单条命令时也可用 `env -u TRANSFORMERS_CACHE -u HF_HUB_CACHE python ...`。

## 典型症状

- server 启动后 GPU 全程 0 MiB、600s timeout 后崩 = 模型从未加载（cache 路径错）
- model 路径指向 `/models/huggingface/transformers/` 而非 `$HF_HOME/hub/`
- `LocalEntryNotFoundError` 但模型确实在 `$HF_HOME/hub/` 下

## OmniServer env_dict 不能删除变量

`OmniServer._start_server()` 做 `env = os.environ.copy(); env.update(self.env_dict)`——**只能覆盖、不能删除**。如果容器设了 `TRANSFORMERS_CACHE`，env_dict 无法 unset 它。

**解法**：在启动 server 的 bash 脚本里 `unset` 这两个变量，或在调起 OmniServer 之前 `os.environ.pop("TRANSFORMERS_CACHE", None)`。

## 历史踩坑

- 2026-04-22 GEBench DiffusionWorker 找不到模型（`TRANSFORMERS_CACHE` 覆盖）
- 2026-04-27 server 600s 超时 GPU 0 MiB（`HF_HUB_CACHE` 覆盖）
