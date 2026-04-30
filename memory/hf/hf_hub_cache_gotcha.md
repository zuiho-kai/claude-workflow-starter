---
name: HF_HUB_CACHE overrides HF_HOME
description: HF_HUB_CACHE 环境变量覆盖 HF_HOME，导致模型找不到，必须 unset
type: feedback
---

进容器后必须同时 unset 两个变量：

```bash
unset TRANSFORMERS_CACHE
unset HF_HUB_CACHE
export HF_HOME=/home/models
```

**Why:** Docker 镜像可能同时设了 `TRANSFORMERS_CACHE` 和 `HF_HUB_CACHE`，两者优先级都高于 `HF_HOME`。只 unset 一个不够。空字符串 ≠ unset。

**How to apply:** 进容器后第一步 `env | grep -iE "cache|hf_home"` 检查，看到任何 CACHE 变量都要 unset。server 启动后 GPU 全程 0 MiB 是典型症状（模型从未加载）。
