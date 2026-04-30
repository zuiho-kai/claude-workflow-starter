---
name: Remote Node General Principles
description: 进入一个陌生远端节点的正确流程（避免假设）
type: feedback
---

# 进入陌生远端节点的正确流程

**错误示范（我犯过的）**：假设新节点路径结构和之前节点一样，直接 `cd /app/vllm-omni` 或 `source <YOUR_REMOTE_WORKDIR>/.venv/bin/activate`，全部踩空。

## 正确顺序

### 1. 先看节点上别人的容器怎么挂的

```bash
docker ps --format "{{.Names}} {{.Image}}"
docker inspect <someone_else_container> --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}'
```

**这比任何文档都权威**。别人容器挂什么，我就挂什么。

### 2. 节点有哪些持久存储

```bash
df -h | grep -E "home|scratch|lustre|nfs"
ls /home /scratch 2>/dev/null
```

Lustre 路径在不同节点可能：
- `/scratch/<YOUR_GROUP>/...`（有 c）
- `/scratch/<SHARED_SCRATCH>/...`（无 c，不存在于 0036）
- `/home/<YOUR_GROUP>/<user>/...`（0036 实际结构）

**不要假设路径。先查文件系统。**

### 3. 节点上有哪些模型缓存

```bash
ls /home/models/hub 2>/dev/null     # Lustre 共享缓存（0036）
ls /scratch/<YOUR_GROUP>/huggingface/hub 2>/dev/null   # Lustre 用户缓存
find /home /scratch -maxdepth 4 -name "models--*" -type d 2>/dev/null | head
```

**模型缓存 160GB，能复用绝不重下**。

### 4. 节点上有没有现成的 vllm-omni clone 和 venv

```bash
find /home/<YOUR_GROUP>/<user> -maxdepth 3 -name vllm-omni -type d 2>/dev/null
ls /app/vllm-omni/.venv 2>/dev/null
which python   # 容器里可能是 /app/vllm-omni/.venv/bin/python
```

### 5. 容器权限问题

容器内是 root，但挂载的 Lustre 目录 owner 是 UID=2129（<YOUR_USERNAME>）。会有两类问题：

- **Git 报 dubious ownership**：`git config --global --add safe.directory "*"`
- **某些 Lustre 子目录 root 没权限读**：没办法，需要容器加 `--user 2129:1033`（但 cuda-12.9 image 可能没建 user，风险高）

## 每次进容器必做

```bash
# 1. 激活 venv（如果 image 预装了）
source /app/vllm-omni/.venv/bin/activate

# 2. 设 HF_HOME（否则模型缓存写 /root/.cache，容器销毁就丢）
export HF_HOME=/home/models

# 3. Git safe directory（容器 root vs 宿主 UID 差异）
git config --global --add safe.directory "*"
```

## 反面教训

- **不要**上来就跑业务命令。先 30 秒探环境。
- **不要**假设节点路径结构。每个节点不一样。
- **不要**挂 `/app`（0006 特例），挂 `/home` 和 `/scratch`。
- **不要**依赖容器内的 `~/.cache`，写 Lustre 才持久。
