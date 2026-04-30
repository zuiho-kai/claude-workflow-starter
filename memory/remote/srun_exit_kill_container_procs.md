---
name: Always kill container processes before exiting srun
description: srun 退出不会杀容器里的进程；退 srun 前必须手动清，否则 GPU 泄漏、同事投诉
type: rule
---

# 规则：退 srun 前必须清容器里的进程

## 根因（一句话）

**Slurm 管 cgroup，docker 管容器，两者不通信**。`docker exec` 创建的进程父进程是宿主 `dockerd`，不在 srun 的 cgroup 里。srun 退出只释放 Slurm 记账和资源权限，**不会带走容器里的进程**。

## 踩过的坑（2026-04-21）

- 上午 srun 到 0006 + 进 `<YOUR_CONTAINER>` 容器跑 pytest gebench
- srun 被打断，shell 退出
- 容器里 `vllm_omni serve` + 4 个 Worker_TP + 若干 multiproc 子进程**全都留着**
- **GPU 0 被占 67GB 一整天**
- 下午另一个用户 srun 上来发现 "说好的空卡呢？" → **同事投诉**

事后（用户手工排查 + 我 docker exec kill）清理时发现容器里 10+ 进程全活着。

## 退 srun 前必做（每次）

在退 srun shell 前，**必须**在容器里确认没有残留：

```bash
# 在 docker exec 进去的 bash 里
ps -eo pid,cmd | grep -E "vllm|Worker_TP|StageEngine|multiprocessing.spawn" | grep -v grep
```

看到任何进程就清：

```bash
# 优雅清（先 TERM 再 KILL）
pkill -TERM -f 'vllm_omni.entrypoints' ; sleep 3 ; pkill -9 -f 'vllm_omni|Worker_TP|StageEngine'

# 验证
ps -eo pid,cmd | grep -E "vllm|Worker_TP" | grep -v grep
# 应该空
```

然后 `exit` 退容器 → `exit` 退 srun。

## 宿主层排查（srun shell 里，不进容器）

```bash
# 看宿主 nvidia-smi 哪些 pid 占 GPU（注意：是宿主 pid，和容器内 pid 不同）
nvidia-smi --query-compute-apps=pid,used_memory,gpu_uuid --format=csv,noheader

# 对照容器里的 pid：docker top 容器名
docker top <YOUR_CONTAINER>
```

## 外部补救（srun 已退出，发现有残留）

需要重新申请一个 srun 到**同一个节点**，然后：

```bash
# 注意 -w / 绕过 cwd permission denied
docker exec -w / <container_id> bash -c 'pkill -9 -f "vllm_omni|Worker_TP"'

# 验证
nvidia-smi --query-gpu=index,memory.free --format=csv,noheader
```

## 系统性规避

### 方法 1：容器里写自杀 trap（推荐）

在 `docker exec` 进容器后第一件事：

```bash
trap 'pkill -9 -f "vllm_omni|Worker_TP|StageEngine" 2>/dev/null' EXIT
```

bash 退出（包括 `exit` 或父 ssh 断开）时自动清子进程。但**仅当这个 bash 是容器里所有 vllm 进程的祖先**时才有效；如果 vllm 是 `nohup`/`&` 脱离 shell 的就不中用。

### 方法 2：pytest 而非手动启 server

`OmniServer` fixture 的 `__exit__` 会 terminate server + 子进程。**pytest 正常结束**（包括 fail）都会清。**被 Ctrl-C 打断时不保证**。

### 方法 3：在 srun shell 里加 trap（兜底）

`~/.bashrc`（宿主 home，不是容器）：

```bash
# 退出 srun shell 时把容器里的 vllm 进程一起带走
if [ -n "$SLURM_JOB_ID" ]; then
    trap '
        for c in $(docker ps --format "{{.Names}}"); do
            docker exec -w / $c bash -c "pkill -9 -f vllm_omni 2>/dev/null" || true
        done
    ' EXIT
fi
```

但这会影响其他人的容器，危险。不推荐启用。

## 记住的判据

退 srun 之前问自己：

1. **容器里 `ps -eo cmd | grep vllm` 是空的吗？** → 不空就 pkill
2. **宿主 `nvidia-smi` 上的 GPU 内存是 0% 吗？** → 不是就去找哪个 pid 还在占
3. **如果我现在 exit，下一个 srun 上来看到的是什么？** → 干净才能退

**这条是硬性规则，不是建议**。漏做一次就占死一张 80GB 卡 + 一个同事的半天。
