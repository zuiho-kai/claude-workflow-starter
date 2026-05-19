---
name: Remote Node 0036 Environment (vs 0006)
description: <NODE> 节点环境和 0006 完全不同，路径结构和挂载都要改
type: reference
---

# <NODE> 节点特性（和 0006 不一样）

**重要：不同节点的路径结构不同，不要假设和 0006 一样。**

## 登录 & 资源

- 登录节点：`fq9hpsacuser03@10.248.12.11`
- 计算节点：`<NODE>`（8× H800 80GB）
- srun：`srun -p <PARTITION> -w <NODE> --gres=gpu:2 --cpus-per-gpu=24 --mem-per-cpu=8G --job-name=<YOUR_JOB> --pty bash`
- 有 slurm 命令，没有 squeue 别名（要用全路径或查别名）

## 路径结构（和 0006 对比）

| 项 | 0006 | 0036 |
|---|---|---|
| 工作目录 | `/app/vllm-omni`（挂载） | `/home/fq9hpsac/fq9hpsacuser03/sources/vllm-omni` |
| venv | `/app/vllm-omni/.venv` | **容器镜像自带**：`/app/vllm-omni/.venv`（cuda-12.9 image 预装） |
| 模型缓存 | `~/.cache/huggingface/hub` | **`/home/models/hub`**（共享 Lustre，持久） |
| GEBench / GEdit | 同上 | `/home/models/hub/datasets--stepfun-ai--GEBench`（已有） |

**不存在的路径（别再假设）**：
- `/scratch/fq9hpsa/w00883325/vllm-omni` ← **这条在 0036 上不存在**！文档里的 `fq9hpsa` 没有 c，实际 Lustre 是 `/scratch/fq9hpsac/`
- `/app/vllm-omni` ← 0036 宿主上 `/app` 是空的，是 0006 的特例挂载

## 容器

### 建容器的正确姿势（0036）

**别人的容器挂 `/home`，不挂 `/app`。跟他们一样。**

```bash
docker run -d --name <YOUR_CONTAINER> --gpus all --ipc=host --network=host \
    --ulimit memlock=-1 --ulimit stack=67108864 \
    -v /home:/home -v /scratch:/scratch \
    -w /home/fq9hpsac/fq9hpsacuser03 \
    taichangzhou/vllm-omni-ci:cuda-12.9 tail -f /dev/null
```

**关键点**：
- `-v /home:/home` 让 `/home/models/hub`（模型缓存）和 `/home/fq9hpsac/fq9hpsacuser03/sources/vllm-omni`（代码）都持久可见
- `-v /scratch:/scratch` 备用（Lustre 另一个挂载）
- **不要挂 `/app`**（0006 特例）
- **image**：`taichangzhou/vllm-omni-ci:cuda-12.9`（30GB 干净 CI 镜像，已预装 vllm-omni 到 `/app/vllm-omni/.venv`）

### 可选 image

| image | 大小 | 特点 |
|---|---|---|
| `taichangzhou/vllm-omni-ci:cuda-12.9` | 29.9GB | 官方 CI 镜像，干净，venv 预装 vllm-omni |
| `vllm-omni/fq9hpsacuser01-omni-dev:v3.3` | 679GB | 同事 01 的 dev 镜像，大但可能有额外缓存 |

## HF_HOME 必须设

**默认 `~/.cache/huggingface` 在容器里 = `/root/.cache/huggingface` = 容器销毁就丢。**

每次进容器第一件事：
```bash
export HF_HOME=/home/models
```

或者写进 `~/.bashrc`（容器里的 `.bashrc` 也会丢，更好的做法是写进持久 bashrc 然后 mount）。

## Git 的 dubious ownership 坑

容器是 root (uid=0)，但 `/home/fq9hpsac/fq9hpsacuser03/sources/vllm-omni` 是 uid=2129。git 会拒绝操作：

```bash
git config --global --add safe.directory "*"
```

## 模型状态（0036 /home/models/hub）

**已有**（不用重下）：
- `tencent/HunyuanImage-3.0` (base, 158GB)
- `hunyuanvideo-community/HunyuanVideo-1.5-Diffusers-480p_t2v`
- `black-forest-labs/FLUX.1-dev` / FLUX.1-Kontext / FLUX.2-dev / FLUX.2-klein-4B
- `ByteDance-Seed/BAGEL-7B-MoT`
- `QuantTrio/Qwen3-VL-30B-A3B-Instruct-AWQ`
- `meituan-longcat/LongCat-Image` / LongCat-Image-Edit
- `stepfun-ai/GEBench` (dataset)
- `stepfun-ai/GEdit-Bench` (dataset)

**需要下载**：
- `tencent/HunyuanImage-3.0-Instruct` (~160GB, ~20 min at 130 MB/s)

下载命令（确保下到 /home/models/hub 持久位置）：
```bash
export HF_HOME=/home/models
hf download tencent/HunyuanImage-3.0-Instruct --cache-dir /home/models/hub
```

## vllm-omni 仓库状态

- 路径：`/home/fq9hpsac/fq9hpsacuser03/sources/vllm-omni`
- **默认 origin 是 `jiangkuaixue123/vllm-omni`**（某 fork，不是 vllm-project 上游）
- HEAD 默认 f81429c（老 main，**不是最新 main**，**不是 PR #2383 之后**）
- 拉我的 CI 分支：
  ```bash
  git remote add claude-fork https://github.com/zuiho-kai/vllm-omni.git
  git fetch claude-fork feat/hunyuan-image3-accuracy-ci
  git checkout -B feat/hunyuan-image3-accuracy-ci claude-fork/feat/hunyuan-image3-accuracy-ci
  ```
