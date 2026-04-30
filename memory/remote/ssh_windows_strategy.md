---
name: Windows SSH strategy for remote server
description: Windows 环境下 SSH 到远端服务器的可靠方案：Windows OpenSSH + key auth + retry
type: feedback
---

用 `/c/Windows/System32/OpenSSH/ssh.exe`（Windows 原生 OpenSSH），不要用 Git Bash 的 `/usr/bin/ssh`。

**Why:** Git Bash SSH 用 ASKPASS 密码认证连续失败会触发 fail2ban；Windows/WSL ControlMaster 均不可用（Unix socket / VPN 兼容问题）；WSL2 NAT 无法访问内网段。

**How to apply:**
```bash
WIN_SSH=/c/Windows/System32/OpenSSH/ssh.exe
ssh_retry() {
  for i in 1 2 3 4 5; do
    out=$($WIN_SSH -o ControlMaster=no -o ConnectTimeout=10 vllm-server "$1" 2>&1)
    [[ "$out" != *"Connection closed"* && "$out" != *"kex_exchange"* ]] && echo "$out" && return 0
    sleep 3
  done; return 1
}
```
- SSH key 必须提前放到服务器（`~/.ssh/authorized_keys`）
- 每次 SSH 尽量打包多条命令，减少连接次数
- 服务器 `MaxStartups` 限制并发连接，快速连多次会随机拒绝，retry 间隔 3s
