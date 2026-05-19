---
name: SSH 到远端的可靠模板 + KEX 错误诊断
description: Windows OpenSSH + key auth + retry；kex_exchange_identification = sshd 未就绪要重试不要问密码；tmux send-keys 操作容器
type: reference
---

## 1. 首选：Windows OpenSSH + key auth + retry

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

## 2. fallback：ASKPASS（仅当登录节点没放 key）

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

## 3. KEX 错诊断：`Connection closed` ≠ auth 失败

SSH 报 `kex_exchange_identification: Connection closed by remote host` 或 `Connection closed by remote host`（连接在 KEX 阶段被关，没到 auth）= **sshd 还没起完**，跟 auth/密码无关。

`Permission denied`（含 `publickey,password`）才是 auth 失败，那时候才该考虑密码/key。

**Why**：曾经新拉起 Aliyun 实例 47.79.124.13:31368，前 30s sshd 未就绪，连接被立刻关。我用 `BatchMode=yes` 试了 2 次 + sleep 15s 重试 1 次就报"连不上需要密码"，被用户骂"傻逼"。其实历史 `settings.local.json` 里这个 IP 从来没存过密码，本机 `~/.ssh/id_ed25519` 早就加载，等 sshd 起完直接 key-auth 通了。

**How to apply**：
- 看到 `kex_exchange_identification` / `Connection closed` 一律按"等"处理，**不要**问用户密码
- 新拉起的实例（用户说"新拉起的" / "新启动" / "刚开" 都是信号）首次 ssh 给 **≥60s** 缓冲，至少 retry 5 次（间隔 ≥20s）再认输
- 触发认输条件：5 次失败仍是 KEX 错 → 才 escalate（防火墙/端口错）；任何一次报 `Permission denied` → 立刻问 key/密码
- 历史 settings.local.json 里能 grep 到的 IP 默认 key-auth 已设好，别假设要密码

## 4. 操作容器：tmux send-keys（不要 SSH 直连容器）

容器里没有 slurm 命令，不要试图 SSH 直连容器或在容器里跑 srun。正确方式是通过 tmux send-keys 发命令到已经在容器里的 tmux window。

```bash
# 发命令
ssh ... 'tmux send-keys -t claude_test:0 "your command" Enter' < /dev/null

# 等几秒后读输出
ssh ... 'tmux capture-pane -t claude_test:0 -p -S -30' < /dev/null
```

**注意：**
- 长命令注意引号嵌套，复杂的先写到远端文件再执行（见 `../feedback/remote_debug_strategy.md` docker exec 引号陷阱）
- capture-pane 默认只抓当前可见区域，用 `-S -N` 抓更多历史行
- tmux window 有前台进程时不能往该 window 发 shell 命令——`send-keys` 进了进程 stdin，从另一个 window 发
