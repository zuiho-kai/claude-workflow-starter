# 2026-04-23 — "释放资源"只杀进程没退 srun

- 编号：`inc-2026-04-23-remote-ssh-slurm-container-04`
- 归属：`framework/remote`
- 状态：已验证
- 搜索词："释放资源"只杀进程没退 srun
- 影响范围：framework/remote

**症状**：pkill 后 Slurm job 一直占着节点
**根因**：srun shell 没退出，job 不会释放
**解法**：三步走 pkill → exit 容器 → exit srun → squeue 确认
