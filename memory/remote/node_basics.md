---
name: 进陌生远端节点的通用流程 / PYTHONPATH 跑别人 editable install
description: 进新节点先 docker inspect + 查文件系统不假设；共享 venv 别人 editable install 时用 git worktree + PYTHONPATH 前置不污染对方
type: feedback
---

## 1. 进陌生远端节点的正确流程

**错误示范（我犯过的）**：假设新节点路径结构和之前节点一样，直接 `cd /app/<your-framework>` 或 `source <YOUR_REMOTE_WORKDIR>/.venv/bin/activate`，全部踩空。

### 正确顺序

#### 1.1 先看节点上别人的容器怎么挂的

```bash
docker ps --format "{{.Names}} {{.Image}}"
docker inspect <someone_else_container> --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}'
```

**这比任何文档都权威**。别人容器挂什么，我就挂什么。

#### 1.2 节点有哪些持久存储

```bash
df -h | grep -E "home|scratch|lustre|nfs"
ls /home /scratch 2>/dev/null
```

Lustre 路径在不同节点可能：
- `/scratch/<YOUR_GROUP>/...`
- `/home/<YOUR_GROUP>/<user>/...`

**不要假设路径。先查文件系统。**

#### 1.3 节点上有哪些模型缓存

```bash
ls /home/models/hub 2>/dev/null     # Lustre 共享缓存
ls /scratch/<YOUR_GROUP>/huggingface/hub 2>/dev/null   # Lustre 用户缓存
find /home /scratch -maxdepth 4 -name "models--*" -type d 2>/dev/null | head
```

**模型缓存 160GB，能复用绝不重下**。

#### 1.4 节点上有没有现成的框架 clone 和 venv

```bash
find /home/<YOUR_GROUP>/<user> -maxdepth 3 -name <your-framework> -type d 2>/dev/null
ls /app/<your-framework>/.venv 2>/dev/null
which python   # 容器里可能是 /app/<your-framework>/.venv/bin/python
```

#### 1.5 容器权限问题

容器内是 root，但挂载的 Lustre 目录 owner 是 UID=2129 之类。会有两类问题：

- **Git 报 dubious ownership**：`git config --global --add safe.directory "*"`
- **某些 Lustre 子目录 root 没权限读**：没办法，需要容器加 `--user 2129:1033`（但 cuda-12.9 image 可能没建 user，风险高）

### 反面教训

- **不要**上来就跑业务命令。先 30 秒探环境
- **不要**假设节点路径结构。每个节点不一样
- **不要**依赖容器内的 `~/.cache`，写 Lustre 才持久

## 2. 别人的 editable install：worktree + PYTHONPATH 前置

远端共享 venv 里的框架包经常是别人活跃 checkout 的 editable install（典型在 `/mnt/scratch/wt-pr<n>/`），上面可能有别人 mid-edit 的脏文件，**不能直接 patch**。

### 套路

1. **建干净 worktree**：从那个 editable install 的目录 fetch upstream/main 后 `git worktree add /mnt/scratch/wt-<my-feature> upstream/main`——detached HEAD 在跟本地完全一致的 commit，不污染对方分支
2. **SCP 自己的改动文件**：改了哪几个就 scp 哪几个进新 worktree 的相同相对路径（不要整目录 sync，否则把对方未 push 的状态也带过去）
3. **PYTHONPATH 前置**跑：
   ```bash
   PYTHONPATH=/mnt/scratch/wt-<my-feature>:$PYTHONPATH python -m pytest <test_path> -v
   ```
   Python 找包按 sys.path 顺序，前置自己的目录 → 我的 `<your-package>/...` 模块文件先被找到，editable install 里的同名模块被屏蔽
4. **验证生效**：`python -c "import <your-package>.X; print(<your-package>.X.__file__)"` 必须打印自己 worktree 路径，不是 `/mnt/scratch/wt-pr<n>/...`

### 适用范围

- 测试 Python 端纯逻辑改动（prompt 构造、schema、validator、DSL）
- 改动只涉及少数 .py 文件（≲10 个），SCP 还能控制
- **不适用**：动 C++ extension / kernel / 编译产物——editable install 的 .so 是另一份、PYTHONPATH 不解决 ABI
- **不适用**：改动牵动 setup.py / pyproject.toml / `__init__.py` 重导出顺序——可能需要重装

### 反例（不要做）

- 直接 `vim /mnt/scratch/wt-pr<n>/<your-package>/...` 改对方 working tree
- `pip install -e .` 自己的 worktree 覆盖对方的 editable
- rsync 整个本地 worktree 上去——会把本地未 commit 的脏文件、pyc 缓存、IDE 配置全推过去
