# Memory · remote/

**何时来翻**：SSH 到远端、进 docker 容器、申请 Slurm、设环境变量、退 srun 之前。新节点先读 `remote_node_general.md` + `no_container_ephemeral.md`。当前节点的 IP / 路径 / 容器名见 `docs/remote_server.md`（非 git tracked），不在 memory 里。

| 文件 | 一句话 |
|------|--------|
| [remote_node_general.md](remote_node_general.md) | 进陌生节点通用流程：先 `docker inspect` 看挂载、查文件系统，别假设路径 |
| [no_container_ephemeral.md](no_container_ephemeral.md) | 容器内一切持久内容写宿主挂载路径，不写 `~/.cache` / `/tmp` / 容器层 |
| [hf_cache_env_gotcha.md](hf_cache_env_gotcha.md) | `TRANSFORMERS_CACHE` / `HF_HUB_CACHE` 都覆盖 `HF_HOME`，必须 unset（空字符串不行） |
| [srun_exit_kill_container_procs.md](srun_exit_kill_container_procs.md) | 退 srun 前必须 `pkill` 容器内进程，三步走（pkill→exit docker→exit srun→squeue 空） |
| [docker_exec_cwd_workaround.md](docker_exec_cwd_workaround.md) | docker exec chdir permission denied → 先 `cd` 到匹配宿主路径再 `exec -it` |
| [steal_idle_gpus.md](steal_idle_gpus.md) | 申请少卡 + 容器 `--gpus all` 偷用空闲 GPU |
| [remote_is_hongkong.md](remote_is_hongkong.md) | 香港机器直连 PyPI，不要清华源（反向绕路慢） |
| [ssh_from_claude.md](ssh_from_claude.md) | Windows OpenSSH + key auth + retry；fail2ban 防御；tmux send-keys 操作容器 |
