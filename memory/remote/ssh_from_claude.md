---
name: 从 Claude 环境 SSH 到远端的可靠模板
description: Windows OpenSSH + key auth + retry + tmux send-keys 操作容器；ASKPASS 仅作 fallback（密码失败会触发 fail2ban）
type: reference
---

## 首选：Windows OpenSSH + key auth

```bash
WIN_SSH=/c/Windows/System32/OpenSSH/ssh.exe
ssh_retry() {
  for i in 1 2 3 4 5; do
    out=$($WIN_SSH -o ControlMaster=no -o ConnectTimeout=10 vllm-server "$1" 2>&1)
    [[ "$out" != *"Connection closed"* && "$out" != *"kex_exchange"* ]] && echo "$out" && return 0
    sleep 3
  done
  return 1
}
```

**Why:**
- Git Bash 的 `/usr/bin/ssh` + ASKPASS 密码失败连续 N 次会触发服务器 fail2ban → IP 被封
- Windows / WSL ControlMaster 不可用（Unix socket / VPN 兼容问题）
- WSL2 NAT 无法访问内网段

**注意：**
- SSH key 必须提前放服务器 `~/.ssh/authorized_keys`
- 服务器 `MaxStartups` 限制并发，快速连多次会随机拒绝 → retry 间隔 ≥ 3s
- SSH 超时后先 `sleep 60` 再试；连续 2 次失败等 5 分钟（避免短连接风暴 + fail2ban）
- 每次 SSH 尽量打包多条命令，减少连接次数

## fallback：ASKPASS（仅当登录节点没放 key）

```bash
ASKPASS_SCRIPT=$(mktemp)
cat > "$ASKPASS_SCRIPT" << 'PWEOF'
#!/bin/bash
echo '<password>'
PWEOF
chmod 700 "$ASKPASS_SCRIPT"

SSH_ASKPASS="$ASKPASS_SCRIPT" SSH_ASKPASS_REQUIRE=force DISPLAY=:0 \
  ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 \
      <user>@<host> '<command>' < /dev/null
```

`< /dev/null` 必须加，否则 SSH 会尝试读 stdin。

## 操作容器：tmux send-keys（不要 SSH 直连容器）

容器里没有 slurm 命令，不要试图 SSH 直连容器或在容器里跑 srun。正确方式是通过 tmux send-keys 发命令到已经在容器里的 tmux window。

```bash
# 发命令
ssh ... 'tmux send-keys -t <YOUR_TMUX_SESSION>:0 "your command" Enter' < /dev/null

# 等几秒后读输出
ssh ... 'tmux capture-pane -t <YOUR_TMUX_SESSION>:0 -p -S -30' < /dev/null
```

**注意：**
- 长命令注意引号嵌套，复杂的先写到远端文件再执行（见 [`remote_debug_strategy.md`](../feedback/remote_debug_strategy.md) docker exec 引号陷阱）
- capture-pane 默认只抓当前可见区域，用 `-S -N` 抓更多历史行
- tmux window 有前台进程时不能往该 window 发 shell 命令——`send-keys` 进了进程 stdin，从另一个 window 发
