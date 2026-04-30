---
name: Remote Compute Node Environment (per-node specifics)
description: 不同节点的路径结构和挂载都不一样，进新节点先按本文件流程探明
type: reference
---

# 计算节点专属环境（占位模板，按节点实例化）

> **首次使用**：把本文件复制成 `remote_0036_env.md`（或按你的节点编号命名，如 `remote_<NODE_TAG>_env.md`），已被 `.gitignore`，填真实信息后保存。多节点环境每个节点一份。

**重要：不同节点的路径结构不同，不要假设和别的节点一样。**

## 登录 & 资源

- 登录节点：`<YOUR_USERNAME>@<LOGIN_NODE_IP>`
- 计算节点：`<COMPUTE_NODE>`（8× <GPU_TYPE> 80GB）
- srun：`srun -p <SLURM_PARTITION> -w <COMPUTE_NODE> --gres=gpu:2 --cpus-per-gpu=24 --mem-per-cpu=8G --job-name=<JOB_NAME> --pty bash`

## 路径结构（和其他节点对比，记下差异）

| 项 | 节点 A（旧） | 节点 B（本节点） |
|---|---|---|
| 工作目录 | `/app/<repo>`（挂载） | `<YOUR_REMOTE_WORKDIR>` |
| venv | `/app/<repo>/.venv` | 容器镜像自带 / 或 `<YOUR_VENV>` |
| 模型缓存 | `~/.cache/huggingface/hub` | `<MODEL_CACHE_DIR>`（共享 Lustre，持久） |
| 数据集 | 同上 | `<DATASET_DIR>` |

**不存在的路径（别再假设）**：
- 列出在本节点 *不存在* 的旧路径，避免 cd 进错地方

## 容器

### 建容器的正确姿势

**进新节点先看别人的容器怎么挂**，跟他们一样。

```bash
docker run -d --name <YOUR_CONTAINER> --gpus all --ipc=host --network=host \
    --ulimit memlock=-1 --ulimit stack=67108864 \
    -v /home:/home -v /scratch:/scratch \
    -w <YOUR_REMOTE_WORKDIR> \
    <DOCKER_IMAGE> tail -f /dev/null
```

**关键点**：
- `-v /home:/home` 让模型缓存和代码都持久可见
- `-v /scratch:/scratch` 备用（Lustre 另一个挂载）
- 别盲目挂 `/app`（特定节点的特例）

### 可选 image

| image | 大小 | 特点 |
|---|---|---|
| `<DOCKER_IMAGE>` | ~30GB | 官方 CI 镜像，干净，venv 预装 |

## HF_HOME 必须设

每次进容器第一件事：
```bash
export HF_HOME=<MODEL_CACHE_DIR>
```

## Git 的 dubious ownership 坑

容器是 root (uid=0)，但挂载目录是宿主用户 uid。git 会拒绝操作：

```bash
git config --global --add safe.directory "*"
```

## 模型状态（按本节点实际情况列）

**已有**（不用重下）：
- 列出共享缓存里已有的模型 / 数据集

**需要下载**：
- 列出待下载条目 + 下载命令（`hf download <repo> --cache-dir <MODEL_CACHE_DIR>`）

## 仓库默认 origin

- 路径：`<YOUR_REMOTE_WORKDIR>`
- **默认 origin 是 `<UPSTREAM_FORK_USER>/<repo>`**（某 fork 还是上游？记下来）
- 拉自己分支：
  ```bash
  git remote add my-fork https://github.com/<YOUR_GITHUB>/<repo>.git
  git fetch my-fork <branch>
  git checkout -B <branch> my-fork/<branch>
  ```
