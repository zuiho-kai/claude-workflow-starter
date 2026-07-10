# 2026-04-27 — sinfo 查空闲 GPU 方法

- 编号：`inc-2026-04-27-remote-ssh-slurm-container-08`
- 归属：`framework/remote`
- 状态：已验证
- 搜索词：sinfo 查空闲 GPU 方法
- 影响范围：framework/remote

**用法**：`sinfo -p <partition> --noheader -o "%n %G %C %t"`
**输出格式**：`%C` = `已分配/空闲/其他/总CPU`，每卡 28 CPU（H800 节点）
**换算**：空闲 GPU = 空闲 CPU ÷ 28
**提醒**：`mixed` 状态 = 部分卡被占；`drain` = 节点下线不可用；不需要申请 allocation 就能看
