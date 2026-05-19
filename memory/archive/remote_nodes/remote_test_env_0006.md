---
name: Remote GPU Test Environment
description: 远端 GPU 服务器测试环境配置，含 slurm 资源申请和 tmux session
type: reference
---

## 远端测试环境

- 登录节点：`fq9hpsacuser03@10.248.12.11`（主机名 `hk01lgn001`）
- 密码：`82!tCb7A4`
- 计算节点：`hk01dgx036`（8× H800 80GB）
- 工作目录：`/scratch/fq9hpsa/w00883325/vllm-omni`

### 资源申请（Slurm）
登录节点有 slurm 命令（srun/scancel/squeue），不需要 ssh 到计算节点。
```bash
# 申请 4 卡
srun -p q-fq9hpsac -w hk01dgx036 --gres=gpu:4 --cpus-per-gpu=24 --mem-per-cpu=8G --job-name=claude_test --pty bash
# 查看 jobs
squeue -u fq9hpsacuser03
# 释放
scancel <job_id>
```
注意：申请前先 scancel 旧 job，否则会排队等资源。

### 两种进入方式
1. **slurm srun**（推荐）：直接 srun 到计算节点，8 卡全可见，不需要 docker
2. **docker exec**：`docker exec -it wzr_omni bash`（需要先 srun 到计算节点）

### tmux sessions
- `claude_test`：我们创建的测试 session
- 用户可能有自己的 session（如 `dyy_debug`、`wzr_work`），不要动

### 已知问题
- 系统 vllm 0.18.0，venv 里 vllm 0.19.0，必须 `source /scratch/fq9hpsa/w00883325/.venv/bin/activate`
- numpy 2.x 与 cv2 不兼容，需要 `pip install "numpy<2"`
- I2T YAML 里 `devices: "2,3,4,5"` 是 TP4，不要额外设 CUDA_VISIBLE_DEVICES（会导致可见 GPU 不够）
- 官方 HF 模型可以正常加载和推理（用 `AutoModelForCausalLM` + `device_map="auto"`）
- VAE 编码需要额外 ~2GB 显存，`device_map="auto"` 分配不当会 OOM
