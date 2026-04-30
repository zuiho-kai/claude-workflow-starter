# Memory · remote/

**何时来翻**：SSH 到远端服务器、进 docker 容器、申请 Slurm 资源、设环境变量、退 srun 之前。新节点先读 `remote_node_general.md` + `no_container_ephemeral.md`。

## 含真实凭证的文件（template 模式）

下面三个走「template + gitignore」套路：仓库里只有 `*.template.md`（占位符版本）；首次启动时 cc 会引导你复制为对应 `*.md` 文件并填真实凭证，实例文件已被 `.gitignore` 不会泄漏。

| Template | 实例（`.gitignore`） | 用途 |
|----------|---------------------|------|
| [ssh_connection_pattern.template.md](ssh_connection_pattern.template.md) | `ssh_connection_pattern.md` | SSH 连接模板（ASKPASS / tmux send-keys / 密码） |
| [remote_test_env.template.md](remote_test_env.template.md) | `remote_test_env.md` | 主测试节点环境（IP / 节点名 / 工作目录 / 分区） |
| [remote_0036_env.template.md](remote_0036_env.template.md) | `remote_<NODE_TAG>_env.md` | 每个计算节点一份，记节点专属路径/挂载 |

## 通用文件（无凭证）

| 文件 | 一句话 |
|------|--------|
| [remote_node_general.md](remote_node_general.md) | 进陌生节点通用流程，先 `docker inspect` 看挂载，别假设路径 |
| [remote_is_hongkong.md](remote_is_hongkong.md) | 香港机器直连 PyPI，不要用清华源 |
| [ssh_windows_strategy.md](ssh_windows_strategy.md) | Windows SSH 策略：用 OpenSSH + key auth + retry |
| [no_container_ephemeral.md](no_container_ephemeral.md) | 容器内一切持久内容写宿主挂载路径，不写容器层 |
| [srun_exit_kill_container_procs.md](srun_exit_kill_container_procs.md) | 退 srun 前必须 `pkill` 容器内进程，不然占死 GPU |
| [docker_exec_cwd_workaround.md](docker_exec_cwd_workaround.md) | docker exec chdir permission denied workaround |
| [transformers_cache_gotcha.md](transformers_cache_gotcha.md) | `TRANSFORMERS_CACHE` 覆盖 `HF_HOME`，必须 `unset`（空字符串不行） |
| [steal_idle_gpus.md](steal_idle_gpus.md) | 申请少卡 + 容器 `--gpus all` 偷用空闲 GPU |
