---
name: Remote GPU Test Environment
description: 远端 GPU 服务器测试环境配置，含 slurm 资源申请和 tmux session
type: reference
---

> **首次使用**：复制为 `remote_test_env.md`（已 `.gitignore`），把占位符替换成你的真实环境。

## 远端测试环境

- 登录节点：`<YOUR_USERNAME>@<LOGIN_NODE_IP>`（主机名 `<LOGIN_NODE>`）
- 密码：`<YOUR_PASSWORD>`
- 计算节点：`<COMPUTE_NODE>`（8× <GPU_TYPE> 80GB）
- 工作目录：`<YOUR_REMOTE_WORKDIR>`

### 资源申请（Slurm）
登录节点有 slurm 命令（srun/scancel/squeue），不需要 ssh 到计算节点。
```bash
# 申请 4 卡
srun -p <SLURM_PARTITION> -w <COMPUTE_NODE> --gres=gpu:4 --cpus-per-gpu=24 --mem-per-cpu=8G --job-name=claude_test --pty bash
# 查看 jobs
squeue -u <YOUR_USERNAME>
# 释放
scancel <job_id>
```
注意：申请前先 scancel 旧 job，否则会排队等资源。

### 两种进入方式
1. **slurm srun**（推荐）：直接 srun 到计算节点，8 卡全可见，不需要 docker
2. **docker exec**：`docker exec -it <YOUR_CONTAINER> bash`（需要先 srun 到计算节点）

### tmux sessions
- `claude_test`：我们创建的测试 session
- 用户可能有自己的 session（如 `<COLLEAGUE_TMUX>`），不要动

### 已知问题（按你的实际环境补充）
- 系统 vllm 版本 vs venv 内版本不一致时，必须 `source <YOUR_VENV>/bin/activate`
- numpy 2.x 与 cv2 不兼容，需要 `pip install "numpy<2"`
- `devices: "2,3,4,5"` 是 TP4，不要额外设 CUDA_VISIBLE_DEVICES
- VAE 编码需要额外 ~2GB 显存，`device_map="auto"` 分配不当会 OOM
