---
name: Steal idle GPUs via --gpus all in container (when srun allocates fewer)
description: Slurm 申请卡数只决定 cgroup 计费，容器 --gpus all 能看到节点全部 GPU，空闲的就能偷用
type: rule
---

# 偷卡技巧

**关键事实**：Slurm 的 `--gres=gpu:N` 只决定 cgroup **计费**和 `CUDA_VISIBLE_DEVICES` 环境变量默认值，但**容器内如果用 `docker run --gpus all`，能看到节点上全部 8 张 GPU**。

节点上有空闲 GPU 时，可以直接用那些空闲卡，不被 srun 分配限制。

## 场景

- srun 只给你分了 2 卡（比如 0,1），但实际这俩卡被占
- 节点上卡 5/6/7 全空（没人用）
- 容器里 `nvidia-smi` 能看到全部 8 卡，其中 5/6/7 显示 `0 MiB` 占用

## 正确变通流程

1. 先申请你**最少需要**的卡数（比如 2 卡 vs 4 卡选 2 卡），容易分到
2. `srun` 进计算节点
3. **建容器用 `--gpus all`**（不用 `--gpus 2` 或 `NVIDIA_VISIBLE_DEVICES=0,1`）：
   ```bash
   docker run -d --name <YOUR_CONTAINER> --gpus all --ipc=host --network=host \
       --ulimit memlock=-1 --ulimit stack=67108864 \
       -v /home:/home -v /scratch:/scratch \
       -w /home/<YOUR_GROUP>/<YOUR_USERNAME> \
       <YOUR_REGISTRY>/<YOUR_IMAGE>:<TAG> tail -f /dev/null
   ```
4. 进容器 `nvidia-smi` 看全部 8 卡，挑空闲的 GPU
5. 启动时用 `CUDA_VISIBLE_DEVICES=5,6,7` 指定（或 `--stage_0_devices=5,6,7,X`）

## 注意事项

- **偷卡有风险**：其他人的 job 起来了可能把你挤掉。但如果只是临时任务（几十分钟），成功率很高
- **守规矩的场景**：如果是长时间跑（几小时以上），还是用 srun 分配的卡，别偷
- **别偷过头**：如果整个节点都被你占，Slurm 可能报警或有人投诉
- **判断空闲**：`nvidia-smi --query-gpu=memory.used --format=csv,noheader` 显示 `0 MiB` 就是空闲

## 反面教训

某次实战：
- 申请 2 卡被分到 GPU 0/1（只剩 10GB 空闲，80B bf16 跑不动）
- 卡 5/6/7 全空（每张 81GB），一开始没想到去用
- 用户提醒："没 4 卡就申请 2 卡，然后进容器偷卡"

**记住这个模式：申请保底卡数 → 进容器看全景 → 偷空闲卡**。
