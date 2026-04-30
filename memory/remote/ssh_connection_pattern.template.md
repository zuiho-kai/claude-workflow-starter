---
name: SSH Connection Pattern for Remote Operations
description: 从 Claude 环境 SSH 到远端必须用 ASKPASS 方式，tmux send-keys 操作容器
type: reference
---

# SSH 连接模式（Claude 环境 → 远端）

> **首次使用**：把本文件复制为 `ssh_connection_pattern.md`（已被 `.gitignore`），把下面占位符替换成你的真实凭证。Claude 进入新会话发现实例文件不存在时会引导你填。

## 认证方式

Claude 环境没有 SSH key 到登录节点，必须用密码 + ASKPASS：

```bash
ASKPASS_SCRIPT=$(mktemp)
cat > "$ASKPASS_SCRIPT" << 'PWEOF'
#!/bin/bash
echo '<YOUR_PASSWORD>'
PWEOF
chmod 700 "$ASKPASS_SCRIPT"

# 所有 SSH 命令都用这个前缀：
SSH_ASKPASS="$ASKPASS_SCRIPT" SSH_ASKPASS_REQUIRE=force DISPLAY=:0 \
  ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 \
      <YOUR_USERNAME>@<LOGIN_NODE_IP> '<command>' < /dev/null
```

## 操作容器的方式

**不要试图 SSH 直连容器或在容器里跑 srun**（容器里没有 slurm 命令）。

正确方式：通过 tmux send-keys 发命令到已经在容器里的 tmux window。

```bash
# 发命令
SSH_ASKPASS=... ssh ... 'tmux send-keys -t claude_test:0 "your command here" Enter' < /dev/null

# 等几秒后读输出
SSH_ASKPASS=... ssh ... 'tmux capture-pane -t claude_test:0 -p -S -30' < /dev/null
```

## 当前 tmux 布局（claude_test session）

- Window 0 (`srun-`): 通常在容器内 `(<env>) root@<COMPUTE_NODE>:...#`
- Window 1 (`slurm`): 登录节点，用于 squeue/sinfo

## 注意事项

- 每次 SSH 都要重新创建 ASKPASS_SCRIPT（mktemp 路径每次不同）
- `< /dev/null` 必须加，否则 SSH 会尝试读 stdin
- tmux send-keys 发长命令时注意引号嵌套，复杂命令先写到远端文件再执行
- capture-pane 默认只抓当前可见区域，用 `-S -N` 抓更多历史行
