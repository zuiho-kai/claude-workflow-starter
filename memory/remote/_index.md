# Memory · remote/

**何时来翻**：SSH 到远端、进 docker 容器、申请 Slurm、设环境变量、退 srun 之前。新节点先读 `node_basics.md` + `container_setup.md`。当前节点的 IP / 路径 / 容器名见 `docs/remote_server.md`（非 git tracked），不在 memory 里。

| 文件 | 一句话 |
|------|--------|
| [node_basics.md](node_basics.md) | 进新节点流程：docker inspect 看挂载 / df 查文件系统 / 找现成 venv 和模型缓存；别人 editable install 用 worktree+PYTHONPATH 前置 |
| [container_setup.md](container_setup.md) | 容器持久化：HF cache `unset TRANSFORMERS_CACHE/HF_HUB_CACHE` 必须做（空字符串 ≠ unset）；所有产出写挂载持久路径；可只读复用完整 root cache，缺失时不要补装到 root/cache；multiprocessing 前 `cd /tmp` |
| [srun_lifecycle.md](srun_lifecycle.md) | 退 srun 三步走：容器 pkill→exit docker→exit srun→squeue 空 |
| [ssh_workflow.md](ssh_workflow.md) | Windows OpenSSH + key auth + retry；`kex_exchange_identification` = sshd 未就绪要 retry；tmux send-keys 操作容器 |
| [hf_offline_mandatory.md](hf_offline_mandatory.md) | 远端 HF 加载（`from_pretrained()` / 框架 init）必须 `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`；大模型开跑前做 cache env + `local_files_only` 预检，root cache 只能只读复用 |
