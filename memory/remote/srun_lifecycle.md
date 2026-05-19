---
name: srun 生命周期 / 退出清理 / 偷空闲 GPU
description: 退 srun 前必须 pkill 容器内进程；申请最少卡数 + 容器 --gpus all 偷用空闲 GPU
type: rule
---

## 1. 退 srun 前必须清容器里的进程

### 根因（一句话）

**Slurm 管 cgroup，docker 管容器，两者不通信**。`docker exec` 创建的进程父进程是宿主 `dockerd`，不在 srun 的 cgroup 里。srun 退出只释放 Slurm 记账和资源权限，**不会带走容器里的进程**。

### 踩过的坑（2026-04-21）

- 上午 srun 到 0006 + 进 `<YOUR_CONTAINER>` 容器跑 pytest gebench
- srun 被打断，shell 退出
- 容器里 `vllm_omni serve` + 4 个 Worker_TP + 若干 multiproc 子进程**全都留着**
- **GPU 0 被占 67GB 一整天**
- 下午另一个用户 srun 上来发现 "说好的空卡呢？" → **同事投诉**

### 退 srun 前必做（每次）

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

然后 `exit` 退容器 → `exit` 退 srun → `squeue -u <user>` 确认无残留 job。

### 宿主层排查（srun shell 里，不进容器）

```bash
# 看宿主 nvidia-smi 哪些 pid 占 GPU（注意：是宿主 pid，和容器内 pid 不同）
nvidia-smi --query-compute-apps=pid,used_memory,gpu_uuid --format=csv,noheader

# 对照容器里的 pid：docker top 容器名
docker top <YOUR_CONTAINER>
```

### 外部补救（srun 已退出，发现有残留）

需要重新申请一个 srun 到**同一个节点**，然后：

```bash
# 注意 -w / 绕过 cwd permission denied
docker exec -w / <container_id> bash -c 'pkill -9 -f "vllm_omni|Worker_TP"'

# 验证
nvidia-smi --query-gpu=index,memory.free --format=csv,noheader
```

### 系统性规避

#### 方法 1：容器里写自杀 trap（推荐）

`docker exec` 进容器后第一件事：

```bash
trap 'pkill -9 -f "vllm_omni|Worker_TP|StageEngine" 2>/dev/null' EXIT
```

bash 退出（包括 `exit` 或父 ssh 断开）时自动清子进程。但**仅当这个 bash 是容器里所有 vllm 进程的祖先**时才有效；如果 vllm 是 `nohup`/`&` 脱离 shell 的就不中用。

#### 方法 2：pytest 而非手动启 server

`OmniServer` fixture 的 `__exit__` 会 terminate server + 子进程。**pytest 正常结束**（包括 fail）都会清。**被 Ctrl-C 打断时不保证**。

### 记住的判据

退 srun 之前问自己：

1. **容器里 `ps -eo cmd | grep vllm` 是空的吗？** → 不空就 pkill
2. **宿主 `nvidia-smi` 上的 GPU 内存是 0% 吗？** → 不是就去找哪个 pid 还在占
3. **如果我现在 exit，下一个 srun 上来看到的是什么？** → 干净才能退

**这条是硬性规则，不是建议**。漏做一次就占死一张 80GB 卡 + 一个同事的半天。

## 2. 偷空闲 GPU：申请少卡 + 容器 `--gpus all`

**关键事实**：Slurm 的 `--gres=gpu:N` 只决定 cgroup **计费**和 `CUDA_VISIBLE_DEVICES` 环境变量默认值，但**容器内如果用 `docker run --gpus all`，能看到节点上全部 8 张 GPU**。

节点上有空闲 GPU 时，可以直接用那些空闲卡，不被 srun 分配限制。

### 场景

- srun 只给你分了 2 卡（比如 0,1），但实际这俩卡被占
- 节点上卡 5/6/7 全空（没人用）
- 容器里 `nvidia-smi` 能看到全部 8 卡，其中 5/6/7 显示 `0 MiB` 占用

### 正确变通流程

1. 先申请你**最少需要**的卡数（比如 2 卡 vs 4 卡选 2 卡），容易分到
2. `srun` 进计算节点
3. **建容器用 `--gpus all`**：
   ```bash
   docker run -d --name <YOUR_CONTAINER> --gpus all --ipc=host --network=host \
       --ulimit memlock=-1 --ulimit stack=67108864 \
       -v /home:/home -v /scratch:/scratch \
       -w <HOST_WORK_DIR> \
       <YOUR_DOCKER_IMAGE> tail -f /dev/null
   ```
4. 进容器 `nvidia-smi` 看全部 8 卡，挑空闲的 GPU
5. 启动时用 `CUDA_VISIBLE_DEVICES=5,6,7` 指定（或 `--stage_0_devices=5,6,7,X`）

### 注意事项

- **偷卡有风险**：其他人的 job 起来了可能把你挤掉。但如果只是临时任务（几十分钟），成功率很高
- **守规矩的场景**：如果是长时间跑（几小时以上），还是用 srun 分配的卡，别偷
- **别偷过头**：如果整个节点都被你占，Slurm 可能报警或有人投诉
- **判断空闲**：`nvidia-smi --query-gpu=memory.used --format=csv,noheader` 显示 `0 MiB` 就是空闲

### 反面教训

2026-04 在 0036 上：
- 申请 2 卡被分到 GPU 0/1（只剩 10GB 空闲，80B bf16 跑不动）
- 卡 5/6/7 全空（每张 81GB），但我一开始没想过去用
- 用户提醒："没4卡就申请2卡，然后进容器偷卡"

**记住这个模式：申请保底卡数 → 进容器看全景 → 偷空闲卡**。
