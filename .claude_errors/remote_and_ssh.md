# Error Book: 远端环境 & SSH

## 2026-04-21 — 假设路径 + HF 缓存丢失
**症状**：docker exec 失败、挂载路径为空、HF 缓存消失
**根因**：不同节点布局不同；容器内 `~` 在容器层，非持久
**侦察三连**：
```bash
docker ps && docker inspect <container> --format '{{range .Mounts}}...'
find /home /scratch -maxdepth 5 -name "snapshots" -type d 2>/dev/null
env | grep -iE "cache|hf_home"
```
**提醒**：建容器挂 `/home`，`HF_HOME` 指向持久路径

## 2026-04-22 — TRANSFORMERS_CACHE 覆盖 HF_HOME
**症状**：模型路径指向 `/models/huggingface/transformers/` 而非 `$HF_HOME/hub/`
**根因**：容器默认设了 `TRANSFORMERS_CACHE`，优先级高于 `HF_HOME`
**关键**：`TRANSFORMERS_CACHE=`（空字符串）≠ `unset`
**解法**：`unset TRANSFORMERS_CACHE`

## 2026-04-23 — multiprocessing spawn 子进程 cwd PermissionError
**症状**：worker 进程启动即崩，父进程报 `EOFError`
**根因**：spawn 模式 `os.chdir()` 到父进程 cwd（Lustre 目录），容器 root 没权限
**解法**：跑命令前 `cd /tmp`
**提醒**：EOFError 时先找 worker 端真正错误

## 2026-04-23 — "释放资源"只杀进程没退 srun
**症状**：pkill 后 Slurm job 一直占着节点
**根因**：srun shell 没退出，job 不会释放
**解法**：三步走 pkill → exit 容器 → exit srun → squeue 确认

## 2026-04-27 — Windows ControlMaster 不可用，ASKPASS 触发 fail2ban
**症状**：ControlMaster 报 `getsockname failed: Not a socket`；密码认证连续失败后被封禁
**根因**：Windows Git Bash / OpenSSH ControlMaster 均不支持；WSL2 NAT 无法访问内网段；ASKPASS 失败触发 fail2ban
**解法**：用 `/c/Windows/System32/OpenSSH/ssh.exe` + SSH key auth + 重试逻辑（5次×3s）；每次 SSH 打包多条命令
**提醒**：服务器 `MaxStartups` 限制并发，快速连多次随机拒绝；key auth 不触发 fail2ban

## 2026-04-27 — 新登录节点 srun 不在 PATH，需 module load
**症状**：`bash: line 1: srun: command not found`
**根因**：部分登录节点用 Environment Modules 管理 Slurm
**解法**：`source /etc/profile && module load slurm/slurm/23.02.7 && srun ...`
**提醒**：进新登录节点先 `module avail 2>&1 | grep -i slurm` 确认模块名

## 2026-04-27 — srun --pty 在非交互 SSH 下报 ioctl 错误但仍能执行
**症状**：`srun: error: ioctl(TIOCGWINSZ): Inappropriate ioctl for device` + `Not using a pseudo-terminal, disregarding --pty option`
**根因**：通过 `ssh host 'cmd'` 非交互方式调用 srun，没有 TTY，--pty 无效
**结论**：不影响命令执行，输出仍然正常返回；忽略这两行错误即可
**提醒**：需要真正交互式 shell 时必须用 tmux，不能靠 ssh host 'srun --pty bash'

## 2026-04-27 — sinfo 查空闲 GPU 方法
**用法**：`sinfo -p <partition> --noheader -o "%n %G %C %t"`
**输出格式**：`%C` = `已分配/空闲/其他/总CPU`，每卡 28 CPU（H800 节点）
**换算**：空闲 GPU = 空闲 CPU ÷ 28
**提醒**：`mixed` 状态 = 部分卡被占；`drain` = 节点下线不可用；不需要申请 allocation 就能看

## 2026-04-27 — 远端命令盲等 210s 不看日志
**症状**：启动 vllm-omni server 后用 `while ! curl health; sleep 5; done` 循环等待，210s 内没有任何输出给用户
**根因**：违反硬规则 #1——远端发命令后必须先短 sleep（≤5s）+ capture 确认启动了
**解法**：后台启动（`nohup ... &`），5s 后 `tail -20` 日志确认无错，再 60s 周期检查
**对未来的提醒**：禁止紧密 poll 循环阻塞 SSH 隐藏输出；每次检查必须打印日志片段

## 2026-04-27 — Siglip2VisionModel 版本不兼容 (transformers 5.6.2)
**症状**：`AttributeError: 'Siglip2VisionModel' object has no attribute 'vision_model'`
**根因**：transformers 5.x 中 `Siglip2VisionModel` 自身就是 vision model，不再有嵌套 `.vision_model`
**解法**：`pipeline_hunyuan_image3.py:114` 去掉 `.vision_model` 后缀
**对未来的提醒**：transformers API 变化频繁，跑新环境先 `python -c "from transformers import X; print(dir(X(...)))"`
