# 远端 GPU 服务器访问

## 首次使用 — 用前必填

把下列 placeholder 替换成你的真实信息（推荐：直接告诉 Claude，让它一次帮你改完）：

| 占位符 | 含义 | 例子 |
|--------|------|------|
| `<YOUR_USERNAME>` | 登录节点 SSH 用户名 | `alice` |
| `<LOGIN_NODE_IP>` | 登录节点 IP / 域名 | `10.x.y.z` |
| `<LOGIN_HOSTNAME>` | 登录节点 hostname | `lgn001` |
| `<COMPUTE_NODE>` | 计算节点 hostname | `dgx036` |
| `<YOUR_REMOTE_WORKDIR>` | 远端持久化工作目录（共享盘） | `/scratch/u01/alice/proj` |
| `<YOUR_CONTAINER_NAME>` | docker 容器名 | `alice_dev` |
| `<YOUR_TMUX_SESSION>` | tmux session 名 | **建议用你的用户名**（避免和别人撞车） |
| `<YOUR_SLURM_PARTITION>` | Slurm 分区名 | `gpu-q` |
| `<YOUR_JOB_NAME>` | Slurm job 名 | `alice` |

## 安全注意

- **租借服务器场景下通常只有密码（无法上传 SSH key）**。安全用密码必须做：
  1. 密码绝不进 git——`.gitignore` 已排除常见敏感文件，自查
  2. 用 ASKPASS 临时脚本（`mktemp` + 权限 700 + 会话结束删除）
  3. `set +o history` 临时关 shell history，避免密码进 `.bash_history`
- 如果你能上传 key（少数 case），优先用 key：`ssh-copy-id <YOUR_USERNAME>@<LOGIN_NODE_IP>`

## 连接信息
- **登录节点**：`<YOUR_USERNAME>@<LOGIN_NODE_IP>`（主机名 `<LOGIN_HOSTNAME>`）
- **密码**：通过环境变量 `$SSH_PASSWORD` 传入（**严禁写进任何 git 跟踪的文件**）
- **计算节点**：`<COMPUTE_NODE>`（8× H800 80GB）
- **远端工作目录**：`<YOUR_REMOTE_WORKDIR>`
- **tmux session 名**：`<YOUR_TMUX_SESSION>`

## 快速连接（新终端 3 步上手）

**Step 1: 创建 ASKPASS**
```bash
ASKPASS_SCRIPT=$(mktemp)
cat > "$ASKPASS_SCRIPT" << PWEOF
#!/bin/bash
echo "\$SSH_PASSWORD"
PWEOF
chmod 700 "$ASKPASS_SCRIPT"
```

> 使用前先设环境变量：`export SSH_PASSWORD='你的密码'`（不要写进 .bashrc 或任何 git 跟踪的文件）
后续所有 SSH 命令都用这个模板（`...` 代表下面这行前缀）：
```bash
SSH_ASKPASS="$ASKPASS_SCRIPT" SSH_ASKPASS_REQUIRE=force DISPLAY=:0 \
  ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
      <YOUR_USERNAME>@<LOGIN_NODE_IP> '<command>' < /dev/null
```

**Step 2: 确认 tmux + GPU 资源**
```bash
# 检查 tmux session 是否存在
... 'tmux has-session -t <YOUR_TMUX_SESSION> 2>/dev/null && echo EXISTS || echo NO_SESSION'

# 如果不存在，创建 tmux 并申请 GPU
... 'tmux new-session -d -s <YOUR_TMUX_SESSION>'
... 'tmux send-keys -t <YOUR_TMUX_SESSION> "srun -p <YOUR_SLURM_PARTITION> -w <COMPUTE_NODE> --gres=gpu:2 --cpus-per-gpu=24 --mem-per-cpu=8G --job-name=<YOUR_JOB_NAME> --pty bash" Enter'
# 等 ~10s 让 srun 分配资源，然后检查
... 'tmux capture-pane -t <YOUR_TMUX_SESSION> -p -S -5'
```

**Step 3: 进入工作环境**
```bash
# 进 docker 容器（模型缓存在里面）
... 'tmux send-keys -t <YOUR_TMUX_SESSION> "docker exec -it <YOUR_CONTAINER_NAME> bash" Enter'
# 激活 venv + 进工作目录
... 'tmux send-keys -t <YOUR_TMUX_SESSION> "source <YOUR_REMOTE_WORKDIR>/.venv/bin/activate && cd <YOUR_REMOTE_WORKDIR>" Enter'
```

## 日常操作模板

```bash
# 在计算节点执行命令
... 'tmux send-keys -t <YOUR_TMUX_SESSION> "<cmd>" Enter'

# 读 tmux 输出（最近 40 行）
... 'tmux capture-pane -t <YOUR_TMUX_SESSION> -p -S -40'

# 上传文件（base64 编码）
B64=$(cat <local_file> | base64 -w 0)
... "tmux send-keys -t <YOUR_TMUX_SESSION> \"echo '${B64}' | base64 -d > <remote_path>\" Enter"

# 下载文件
... 'ssh -o ConnectTimeout=10 <COMPUTE_NODE> "docker exec <YOUR_CONTAINER_NAME> cat <remote_path>"'
```

## 资源管理（Slurm）

```bash
# 查看当前 jobs
squeue -u <YOUR_USERNAME>
# 释放旧 job
scancel <job_id>
```

## 注意事项
- 登录节点没有 docker/nvidia-smi，GPU 操作必须通过 srun 到计算节点
- `tmux send-keys` 会直接影响用户正在看的 pane，自己开 session 用
- AR 模型 TP4 每卡 ~41 GiB，`gpu_memory_utilization` 至少 0.9+
- I2T YAML 里 `devices: "2,3,4,5"` 指定了 TP4 设备
- **必须** `source .venv/bin/activate`（vllm 0.19），不要用系统 python
- 跑测试前先 `pip install "numpy<2"`（cv2 兼容）
