---
name: hf-offline-mandatory
description: 远端跑任何 HF 模型加载前必须 export HF_HUB_OFFLINE=1 + TRANSFORMERS_OFFLINE=1；只设 HF_HOME 不够，hub 仍会校验 revision / 拉缺失 shard，大模型一启动就把网络+磁盘打爆
type: rule
---

# 远端 HF 加载必须 OFFLINE

## 规则

任何远端 / 容器内的 HF 模型加载入口（`Omni()` / `from_pretrained()` / `LLM()` / `AutoTokenizer.from_pretrained()`）启动前**必须**两条并行设置：

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
# datasets 也用时加上：
export HF_DATASETS_OFFLINE=1
```

或者直接传**本地绝对快照路径**：

```python
# Pass local absolute snapshot path instead of repo id
model = YourFramework(model="/data/models/hub/models--<org>--<repo>/snapshots/<commit_hash>", ...)
# 而不是
model = YourFramework(model="<org>/<repo>", ...)  # ← 哪怕 HF_HOME 指向已有 cache，仍可能联网  # ← 哪怕 HF_HOME 指向已有 cache，仍可能联网
```

## Why

**设了 `HF_HOME` 不等于不联网**。即使 `$HF_HOME/hub/models--<org>--<repo>/snapshots/<hash>/` 完整存在：

- HF Hub 库仍会去 hub.huggingface.co 校验该 revision 是否有更新
- 任何 shard 不齐 / 哈希校验失败 → 自动重新下载
- 远端节点墙外网络 + 大模型（） → **网络打满 + 磁盘 IO 打爆 → SSH 抖到 kex_exchange_identification 断开**

这跟 `TRANSFORMERS_CACHE / HF_HUB_CACHE 覆盖 HF_HOME` 的坑（A8 / [container_setup §2](container_setup.md)）是**两件事**：
- A8 是「路径被覆盖找不到 cache」
- 本条是「路径对，但仍联网校验导致重下」

## How to apply

### 触发场景

- 远端 / 容器内**任何** `python ... profile / bench / generate / inference` 命令
- 远端 `from_pretrained(...)` / 框架 init 调用 调用前
- 写远端启动包装脚本时（`run_remote.sh` 等）

### 三层防御

1. **shell export**：每次 SSH 进容器 / 进 venv 后第一组命令里加：
   ```bash
   export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
   ```

2. **包装脚本兜底**：远端启动脚本统一封装，offline 三件套写死：
   ```bash
   #!/bin/bash
   set -e
   export HF_HUB_OFFLINE=1
   export TRANSFORMERS_OFFLINE=1
   export HF_DATASETS_OFFLINE=1
   # 校验快照存在，否则拒绝运行
   SNAP="$HF_HOME/hub/models--<org>--<repo>/snapshots"
   [ -d "$SNAP" ] || { echo "FATAL: snapshot missing at $SNAP"; exit 2; }
   exec "$@"
   ```

3. **传本地绝对路径**：测试脚本里直接给 `model=` 一个 `/data/models/hub/.../snapshots/<hash>` 的具体路径，连 repo id 都不写。

### 验证（每次新 venv / 新会话第一条命令）

```bash
env | grep -E "HF_HUB_OFFLINE|TRANSFORMERS_OFFLINE|HF_HOME"
# 期望同时看到：
#   HF_HUB_OFFLINE=1
#   TRANSFORMERS_OFFLINE=1
#   HF_HOME=<existing cache root>
```

任何一个缺失就**别跑模型加载命令**。

## 历史踩坑

- 新建 venv 跑 profile 脚本，只设 `HF_HOME=/data/models` 没设 offline，模型疑似触发重新下载 → 磁盘 IO + 网络拉满 → SSH `kex_exchange_identification: Connection closed by remote host`，5 分钟内连不上服务器
- 类似坑参见 [[container_setup]] §2（cache 路径覆盖）

## 相关

- [[container_setup]] §2：`TRANSFORMERS_CACHE` / `HF_HUB_CACHE` 优先级覆盖 `HF_HOME`（同根问题：cache 配置不到位）
- CLAUDE.md A11
