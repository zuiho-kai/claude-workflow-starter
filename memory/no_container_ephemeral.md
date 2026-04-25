---
name: Always write to mounted host paths, never container ephemeral paths
description: 下载/缓存/产出永远写到宿主挂载 Lustre 路径，不写容器临时路径
type: rule
---

# 核心规则

**容器是临时的。只有挂载的宿主路径才持久。**

凡是有价值的东西（模型、数据集、venv、代码、产出），**第一次下载 / 生成时就写到挂载的 Lustre 路径**，绝对不写容器临时路径。

## 典型错误（我的野鸡程序员习惯）

| 场景 | ❌ 野鸡做法 | ✅ 正确做法 |
|---|---|---|
| 下 HF 模型 | `hf download ...`（默认 `~/.cache/huggingface` = 容器里 `/root/.cache`，**容器删就丢**） | `export HF_HOME=/home/models` **先**，再 `hf download --cache-dir /home/models/hub` |
| pip install | `pip install foo`（进 `/usr/lib/python*/site-packages` = 容器层，重建丢） | venv 放 `/home/<user>/venvs/xxx` 或直接用镜像自带 `/app/vllm-omni/.venv`（在 image 里但不会因 `docker rm` 丢；注意区分） |
| git clone | `git clone ... /tmp/foo` 或 `~/foo` | clone 到 `/home/<YOUR_GROUP>/<user>/sources/` |
| 临时输出 | `/tmp/output.json` | `/home/<user>/workspace/output.json` |
| HuggingFace datasets | `~/.cache/huggingface/datasets` | `/home/models/hub` 下的 `datasets--*` 条目，跟模型放一起 |
| benchmark results | 当前目录（容器 cwd） | `/home/<user>/bench_results/` |

## 每次进容器第一套命令

```bash
# 1. 持久 HF 缓存
export HF_HOME=/home/models

# 2. 持久 pip/uv 缓存（避免下一次重装时重新下）
export PIP_CACHE_DIR=/home/<YOUR_GROUP>/<YOUR_USERNAME>/.cache/pip
export UV_CACHE_DIR=/home/<YOUR_GROUP>/<YOUR_USERNAME>/.cache/uv

# 3. 持久 torch hub / torch compile
export TORCH_HOME=/home/<YOUR_GROUP>/<YOUR_USERNAME>/.cache/torch

# 4. 持久 HF datasets
export HF_DATASETS_CACHE=/home/models/hub  # 跟模型放一起

# 5. Git 共享目录放行
git config --global --add safe.directory "*"
```

## 反面教训

- 每次容器重建，`~/.cache` 就空了，用户问"为什么 hf 目录每次重启都没了"
- 160GB 模型重下一次 20 分钟，没必要
- pip 重装也一样，应该缓存

## 判断标准（每次下东西前问自己）

1. **这个东西下一次还会用到吗？** → 会 → 写挂载路径
2. **容器销毁后是否能再次获得？** → 不能（如下载 token、手动调整过的配置） → 必须写挂载路径
3. **是否超过 100MB？** → 是 → 写挂载路径（省网络）
4. **是否和其他人能共享？** → 是 → 写 `/home/models` 或 `/scratch/<YOUR_GROUP>/huggingface` 共享缓存

**任意一条回答"是"，都不能写容器临时路径。**
