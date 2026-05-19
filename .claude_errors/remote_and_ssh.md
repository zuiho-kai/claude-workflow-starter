# Error Book: 远端环境 & SSH

## 2026-05-19 — 小 lint 修复不该默认上远端复验
**症状**：CI 报 `ruff check` 的 F841 未使用变量，本地删除变量后已经跑过覆盖改动文件的 `ruff check` 和 `py_compile`，但我又默认 SSH 到 `/home/wzr/wt-hunyuan-it2i-ar-stream` 远端复验，结果远端 venv 缺 ruff binary，白白引入环境噪音。
**根因**：把“远端验证流程要规范”（A12）误用成“任何修复都必须远端验证”。这次问题是纯静态 lint，小范围一行删除，本地 ruff 已经命中同一个检查；远端不提供额外信号，反而增加 venv/tooling 变量。
**解法**：小范围 lint/static 修复：本地跑对应 hook/ruff + 必要语法检查即可；只有本地缺依赖、GPU/e2e、远端环境相关、或用户明确要求时才上远端。
**对未来的提醒**：验证要匹配风险来源。代码行为/GPU/环境问题用远端；格式、未使用变量、PR 文档、纯文本规则更新优先本地闭环。不要用“多跑远端”伪装严谨。

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

## 2026-05-14 — cp -r 复制别人的 venv 想"独立"反而踩坑
**症状**：用户在新节点（`root@106.15.124.84:31449`）要求"new own venv"，我没用 `uv venv` 而是 `cp -r /data/wzr/venv .venv`，8.8GB 源拷成 25GB+ 还没生成 `bin/python`，半天动不了。换 `cp -rP` 重试仍然异常膨胀
**根因**：venv 是 "site-packages 指针 + wheel 安装记录" 的元数据集合，不是普通目录。cp 行为受 symlink / uv cache / 并行 fs 语义影响（cpfs 这次明显异常）。更根本的——**复制后仍然不是"own"，只是别人 venv 状态的 fork**。用户的"new owner venv"字面就是 `uv venv` 从零建一个
**解法**：永远走
```bash
cd /<my-new-project-dir>
uv venv .venv --python <existing system python>
.venv/bin/uv pip install vllm==<EXACT_VERSION>      # 命中 uv wheel cache 秒过
.venv/bin/uv pip install -e . --no-build-isolation  # vllm-omni 不在 requirements pin vllm，确认过
```
**对未来的提醒**：(1) 看到 "new"/"own"/"独立 venv" → 自动 `uv venv` 不要找捷径；(2) `du -sh source` vs `du -sh dest` 差异 >1.5x → 立刻停手反问"是不是走错路"；(3) 用户第一次骂之后**还原意图**（uv venv 新建）而不是"换个差不多的动作"（cp 复制）继续硬上 — 这是 P2 派生 / B4 反例

## 2026-05-18 — vLLM-Omni main 升到 vLLM 0.21 后只装 vllm 本体不够

**症状 1**：`upstream/main` 拉到 PR #3630 后，跑 HunyuanImage3 I2T 还没加载模型就 import 崩：
```text
ImportError: cannot import name 'split_routed_experts'
from vllm.model_executor.layers.fused_moe.routed_experts_capturer
```

**根因 1**：代码已经基于 vLLM 0.21 API，但远端现有 venv 仍是 vLLM 0.20.0 / 0.20.2；这些版本没有 `split_routed_experts`。

**解法 1**：在当前 worktree 建自己的 `.venv`，不要改共享 venv：
```bash
cd /tmp
uv venv --python /usr/bin/python3 --system-site-packages /home/wzr/wt-i2t-test-fix/.venv
uv pip install --python /home/wzr/wt-i2t-test-fix/.venv/bin/python --no-deps -U 'vllm==0.21.0'
```
然后验证：
```python
import importlib, vllm
m = importlib.import_module("vllm.model_executor.layers.fused_moe.routed_experts_capturer")
print(vllm.__version__, hasattr(m, "split_routed_experts"))
```

**症状 2**：只装 `vllm==0.21.0 --no-deps` 后，worker 初始化阶段崩：
```text
ImportError: cannot import name 'BatchDecodeWithPagedKVCacheWrapper' from 'flashinfer'
```

**根因 2**：`--system-site-packages` 让新 venv 捡到了系统路径里的残缺/旧 `flashinfer` namespace；而 `vllm==0.21.0` metadata 要求：
```text
flashinfer-python==0.6.8.post1
flashinfer-cubin==0.6.8.post1
```
只装 vLLM 本体不会补这些依赖。

**解法 2**：
```bash
cd /tmp
uv pip install --python /home/wzr/wt-i2t-test-fix/.venv/bin/python --torch-backend cu130 \
  'flashinfer-python==0.6.8.post1' 'flashinfer-cubin==0.6.8.post1'
```
安装后确认：
```python
import flashinfer
print(flashinfer.__version__, hasattr(flashinfer, "BatchDecodeWithPagedKVCacheWrapper"))
```

**注意**：这次 `uv pip install flashinfer...` 顺手把 `.venv` 里的 torch 拉到了 `2.12.0+cu130`，而 vLLM 0.21 metadata 要 `torch==2.11.0`，系统路径已经有 `2.11.0+cu130`。要卸掉 venv 内覆盖的 torch/triton，让它回落到系统 site-packages：
```bash
uv pip uninstall --python /home/wzr/wt-i2t-test-fix/.venv/bin/python torch torchaudio torchvision triton
```
再确认：
```text
torch 2.11.0+cu130
vllm 0.21.0
flashinfer-python 0.6.8.post1
```

**怎么避免**：
1. vLLM-Omni main import 新 vLLM symbol 失败时，先查 vLLM 版本和 symbol 是否存在，不要开始改源码：
   ```bash
   python - <<'PY'
   import importlib, vllm
   print(vllm.__version__)
   m = importlib.import_module("vllm.model_executor.layers.fused_moe.routed_experts_capturer")
   print(hasattr(m, "split_routed_experts"))
   PY
   ```
2. 用 `uv pip install --no-deps vllm==X` 后，必须查 `importlib.metadata.requires("vllm")` 里和 CUDA kernel 相关的 hard deps（flashinfer / torch / triton），逐项补齐或确认系统已有。
3. `--system-site-packages` 是为了复用大体积 torch/CUDA 包，但它也会暴露系统残缺 namespace。遇到奇怪 `ImportError: cannot import name ... from flashinfer (unknown location)`，先看 `flashinfer.__file__` 和 distribution version。
4. 用户明确说"新建 venv，把旧的干掉"时，只删除当前 worktree 自己的 `.venv`；删除前 `readlink -f` 确认路径在 worktree 内，绝不碰共享 `/home/wzr/vllm-omni/.venv`。

## 2026-05-18 — 跑 TP=2 要避开测试 helper 的全局 GPU cleanup/占卡假设

**症状**：用户要求 `tp=2 2,3卡`，但初次跑 pytest helper 仍等待 GPU 0/1/2/3 全部低于 5% 显存，且之前 0/1 上有别人的 TTS vLLM 服务；后来测试结束时 helper 还尝试清理它识别到的 `VLLM::StageEngineCoreProc`。

**根因**：测试 helper 的 GPU memory monitor / residual vLLM cleanup 是全局 0..N 视角，不知道当前 YAML 只用 devices `2,3`。Hunyuan stage config 控制运行设备，但 pytest fixture 的 pre/post cleanup 仍看整机。

**解法**：
- 按用户要求生成临时 YAML，把 `devices: "0,1,2,3"` 改成 `"2,3"`，`tensor_parallel_size: 4` 改成 `2`。
- 跑前用 `nvidia-smi --query-compute-apps` 和 `pgrep -af` 明确哪些进程是自己的，哪些是别人的服务。
- 如果 0/1 有他人服务，不要主动 kill；如果 helper 最后 kill 了残留，要在汇报里说明。

**怎么避免**：
1. 跑非全卡测试前，明确区分三层设备配置：YAML `runtime.devices`、`tensor_parallel_size`、pytest helper cleanup 的全局 GPU 视角。
2. 看到 pre-test monitor 等 0/1 卡，不要误判 TP=2 没生效；看 stage log：`Stage-0 set runtime devices: 2,3` 才是运行路径证据。
3. 多用户机器上，`pkill -f vllm` 这种全局命令禁用；只 kill 自己刚启动的 PID / stage proc。

## 2026-05-18 — GPU 占用判断只看 memory.used 漏了潜伏中的别人进程

**症状**：`nvidia-smi --query-gpu=memory.used` 全是 4 MiB，自信报"4 卡全空"，启动 HunyuanImage3 4 卡 deploy 之后 DiT 在 GPU 2,3 OOM；查 compute-apps 才发现别人有 `end2end.py text2img` 已经 spawn 但 model 还没完全 load（瞬时只占几 MB）。前后浪费 ~5 分钟用户问"我看没人跑"才回头复查。

**根因**：`memory.used` 是 PyTorch reservation 的瞬时值，进程启动到 model load 之间有几十秒 GPU 几乎空。判断 GPU 是否"我的"必须同时看：
- `nvidia-smi --query-gpu=memory.used` —— 当下已分配
- `nvidia-smi --query-compute-apps=pid,process_name,gpu_uuid,used_memory` —— 已注册到 driver 的进程
- `ps -ef | grep -E "(hunyuan|end2end|vllm|VLLM::)"` —— 包括刚 spawn 还没 attach kernel 的 python 进程

**解法**：跑前三件套并行查；用 `nvidia-smi --query-gpu=index,uuid` + compute-apps 的 gpu_uuid 列做映射，确认哪个物理 GPU 是哪个 worker 的。

**怎么避免**：
1. 远端跑 GPU job 前必跑"三件套"：`memory.used` + `compute-apps` + `ps -ef | grep python`，缺一不可。
2. 不要在用户说"全空"之后跳过自查。用户可能基于上一刻看到的状态，跟你眼下抢卡的窗口不重叠。
3. 三件套写成脚本，会话开头跑一次：`bash gpu_owner_check.sh`，输出三类一起看。

## 2026-05-18 — 端到端 smoke 撞 vllm scheduler API 漂移，单测能过但真跑崩

**症状**：本次 PR (#3626 HunyuanImage3 infer_align_image_size) 单测在 `wt-i2t-test-fix/.venv` (vllm 0.21.0) 全过，真跑 `end2end.py img2img` 时 `OmniARAsyncScheduler` 调 `self._get_routed_experts(request)` AttributeError 立刻 die。换 `vllm-omni-pr3444-online-prompt-align/.venv` (vllm 0.20.2) → DiT forward 时 flashinfer ninja JIT `fused_moe_90` 失败。

**根因**：
- 仓库 HEAD 写的代码暗中假设了 upstream vllm 的某个版本（`_get_routed_experts` 是 0.20.x 的；0.21.0 不存在）。
- "单测过"覆盖的只是被改动的 hot path（mm_processor / sampler / postprocess），不会触碰 scheduler + DiT forward。
- venv 是别的 PR 留下来的，没人保证跟你 PR 的 vllm 期望一致。

**解法**：
1. rebase 到主干（main 当前已对齐 vllm 0.21.0），仓库代码、venv、upstream 三方对齐后端到端通。
2. 真正修复路径不是改 venv 也不是 stub 接口，是 git rebase origin/main。

**怎么避免**：
1. **venv 健康检查脚本**：选 venv 前先跑
   ```bash
   $venv/bin/python -c "
   import vllm; print('vllm:', vllm.__version__)
   from vllm.v1.core.sched.scheduler import Scheduler
   print('_get_routed_experts:', hasattr(Scheduler, '_get_routed_experts'))
   import flashinfer; print('flashinfer:', flashinfer.__version__)
   "
   ```
   把"仓库 HEAD 期望调用的 upstream symbol"逐项 hasattr 一遍，3 秒钟决定 venv 配不配。
2. **单测过 ≠ 真跑过**：单测只覆盖 mm_processor / postprocess 这类窄路径；scheduler + forward + KV transfer + connector 整链路必须真跑一次。声明 PR "已验证"前必须有 end-to-end 真跑证据。
3. **PR 长时间未 rebase + main 升了 vllm 大版本**：先 `git rev-list --count main..HEAD --left-right` 看 behind 数；behind ≥ 20 且涉及 vllm 主版本变化时，先 rebase 再调试，别拿旧 venv 硬试。
4. PR 描述里要标注"在 vllm X.Y.Z 上验证过"；reviewer 看到 vllm 版本不匹配可以直接打回。

## 2026-05-18 — 跨主机同步代码用 patch/scp 走弯路，git push/fetch 才是正路

**症状**：Windows 本地改完代码想同步到远端 worktree，先试 `git diff | ssh apply -`（上下文不匹配失败）、再想 scp，最后才用 git commit + push fork branch + 远端 `git fetch + git checkout` 才稳定。中间反复 retry 占 5+ 分钟。

**根因**：纠结于"调试期不要 commit-push 循环"（B1）而绕远路。但 B1 管的是"fix attempt N"型的本地循环；**跨主机同步代码**本来就只有 git 这一条正路。

**解法**：跨主机同步用 git commit + push to fork branch + remote git fetch + git checkout FETCH_HEAD。`git diff | ssh apply` 在 line ending / 文件未保存 / context 漂移时必跪。

**怎么避免**：
1. B1 边界：单机本地试错走 `/tmp/test_xxx.py`；跨主机同步走 commit-push-fetch，禁用 patch/scp。
2. 远端 worktree 在 detached HEAD 时也可以 `git checkout -B branch FETCH_HEAD` 切干净。
3. fork 推送命令本地起好别名：`git remote add fork ...`；push 用 `git push fork HEAD:<branch> --force-with-lease`。

## 2026-05-18 — gh CLI token keyring 失效，PR 描述更新需手贴

**症状**：`gh pr edit 3626 --body-file ...` 报 `Failed to log in to github.com account zuiho-kai (keyring) - The token in keyring is invalid`。

**根因**：Windows 上 gh 的 keyring 存的 token 过期或被替换。本会话内无法刷新。

**解法**：把 PR 描述写成 markdown 文件（如 `.scratch_pr_body.md`），让用户在 GitHub Web 端 Edit → 粘贴。

**怎么避免**：
1. 会话内 `gh auth status` 一次失败 → 标记本会话 gh 不可用，后续 PR 描述/comment 操作直接走"写 markdown + 让用户手贴"。
2. 不要每次有 PR 操作都试一遍 gh，浪费一轮对话。
3. PR 描述文件命名 `.scratch_pr_body.md` 放 worktree 根，未 commit（worktree 一般已 ignore 隐藏文件或 .scratch/ 目录）。

## 2026-05-19 — 远端验证前没读 remote_server.md，错过指定 venv

**症状**：用户给 `ssh root@106.15.124.84 -p 31140` 让我验证，我直接连上后扫 `python --version` / `find` 环境，报默认 `python` 不存在，然后才被用户指出 `docs/remote_server.md` 已写明 `/home/wzr` 下的工作目录和 venv。

**根因**：把“SSH 能连通”误当作“远端环境已知”，跳过了仓库已经维护的远端事实源。`CLAUDE.md` 虽然要求远端侦察，但当前节点 B 的 venv、worktree、同步方式都集中在 `docs/remote_server.md`，不读就会重复踩：错 venv、错目录、错同步方式。

**解法**：任何远端验证 / GPU smoke / 远端 pytest 之前，先读：
```powershell
Get-Content -Encoding utf8 docs\remote_server.md
```
然后以 `/home/wzr` 为稳定锚点。用户明确预期是：**本地修改先 commit + push 到远程分支；服务器在 `/home/wzr` 下新建本次专用 worktree 和 venv；远端通过 git fetch/pull 同步代码后验证**。不能把某个旧 `wt-*` 或 `.venv` 当永久路径（用户会不定期删除 worktree 和 venv）。

先动态查看当前 `/home/wzr`，避免命名冲突：
```bash
ls -la /home/wzr
find /home/wzr -maxdepth 3 -type f \( -name pyvenv.cfg -o -name activate \) 2>/dev/null | sort
find /home/wzr -maxdepth 2 -type d -name "wt-*" 2>/dev/null | sort
```
再新建本次专用目录（名字按任务改）：
```bash
cd /home/wzr
git clone <repo-url> wt-<task>   # 若已有合适 repo，可 git fetch 后 git worktree add /home/wzr/wt-<task> <branch>
cd /home/wzr/wt-<task>
git fetch origin <branch>
git checkout -B <branch> FETCH_HEAD
uv venv .venv --python /usr/bin/python3 --system-site-packages
```
新建 venv 后必须跑健康检查，健康检查通过才继续：
```bash
VENV=/home/wzr/wt-<task>/.venv
$VENV/bin/python -c "
import vllm; print('vllm:', vllm.__version__)
from vllm.v1.core.sched.scheduler import Scheduler
print('_get_routed_experts:', hasattr(Scheduler, '_get_routed_experts'))
import flashinfer; print('flashinfer:', flashinfer.__version__)
"
```

**怎么避免**：
1. 远端命令第一步不是 `ssh ... "pwd"`，而是本地读 `docs/remote_server.md`；除非文件不存在，才问用户远端布局。
2. `/home/wzr` 是稳定目录；每次远端验证默认在 `/home/wzr` 下新建本次专用 worktree 和 `.venv`，不要复用可能被删除的旧路径。
3. 读完必须在执行记录里显式带上三个值：远端 worktree、venv 路径、代码同步分支。
4. 节点 B 同步代码只走 git：本地 commit + push fork branch，远端 `git fetch` + `git checkout -B <branch> FETCH_HEAD`；禁 `scp` / `git diff | ssh apply`。
5. venv 健康检查通过前，不跑 pytest / server / smoke；默认 `python` 不存在或系统 python 不相关都不能作为结论。
6. Windows PowerShell 不能用 Bash 风格 `cmd1 && cmd2`；本地 git 操作分开跑，或用 PowerShell 的语法显式判断 `$LASTEXITCODE`。

## 2026-05-19 — PowerShell 到 SSH 投递脚本：变量展开 / 空文件 / BOM 三连坑

**症状**：跑 PR #3606 远端性能验证时，第一次通过 PowerShell heredoc 投递 `/tmp/run_pr3606_eval.sh`，远端脚本变成 0 字节；另一次脚本首行带 UTF-8 BOM，远端报 `/tmp/run_pr3606_eval.sh: line 1: ﻿#!/usr/bin/env: No such file or directory`。之前还出现过 `$VENV` 被本地 PowerShell 展开，导致远端脚本拿不到期望变量。

**根因**：
- PowerShell 双引号 / here-string 会在本地先展开 `$VENV`、`$()` 等内容。
- Windows 写文本默认可能带 BOM；bash 把 BOM 当作 shebang 前的不可见字符。
- 只看 `nohup ... & echo $!` 只能说明 shell 接受了命令，不说明脚本内容正确或程序已启动。

**解法**：
1. 复杂远端脚本优先本地生成无 BOM 文件，或用单引号 here-string，并在远端落盘后立刻检查：
   ```powershell
   @'
   #!/usr/bin/env bash
   set -euo pipefail
   echo "$VENV"
   '@ | ssh ... 'cat > /tmp/run_x.sh && perl -i -pe "s/^\xEF\xBB\xBF//" /tmp/run_x.sh && chmod +x /tmp/run_x.sh && wc -c /tmp/run_x.sh && sed -n "1,40p" /tmp/run_x.sh'
   ```
2. 后台启动后必须短 sleep + tail 日志确认已经进入程序日志，而不是只看 PID：
   ```bash
   nohup bash /tmp/run_x.sh > /tmp/run_x.log 2>&1 < /dev/null &
   echo $! > /tmp/run_x.pid
   sleep 5
   tail -80 /tmp/run_x.log
   ```

**怎么避免**：
1. PowerShell→SSH→bash 链路中，任何 `$VAR` 都默认有本地展开风险；能单引号就单引号，不能单引号就转义。
2. 远端脚本启动前固定三连：`wc -c`、`sed -n '1,40p'`、`bash -n`。
3. 看到日志 0 字节或没有程序首行 marker，先修脚本投递，不要继续分析模型 / venv / profiler。

## 2026-05-19 — 远端路径不能猜：模型 snapshot 不等于 deploy config 所在地

**症状**：PR #3606 验证脚本假设 HunyuanImage3 snapshot 下存在 `/root/.cache/.../snapshots/<sha>/deploy.yaml`，实际没有，`make_pr3606_config.py` 直接 `FileNotFoundError`。真实 deploy yaml 在代码仓库的 `vllm_omni/deploy/hunyuan_image3_ar.yaml` / `hunyuan_image3.yaml`。

**根因**：把“模型权重 snapshot”误当成“运行部署配置源”。vLLM-Omni 的 deploy YAML 是仓库代码配置，不是 HF checkpoint 的固定组成部分；不同任务（AR-only / full AR+DiT / DiT-only）还对应不同 YAML。

**解法**：远端写 config patch 前先查真实路径：
```bash
find /home/wzr -maxdepth 4 \( -name "*hunyuan*yaml" -o -name "deploy*.yaml" -o -name "*image3*.yaml" \) -print
find /root/.cache/huggingface/hub/models--tencent--HunyuanImage-3.0-Instruct -maxdepth 4 \( -name "*.yaml" -o -name "*.yml" \) -print
```
然后按 workload 选 YAML：AR-only profiling 用 `vllm_omni/deploy/hunyuan_image3_ar.yaml`；全链路 img2img/t2i 用 `vllm_omni/deploy/hunyuan_image3.yaml`。

**怎么避免**：
1. 远端所有路径先 `ls/find` 实证，尤其是模型 snapshot、deploy config、测试图片、venv。
2. PR 性能验证脚本里把 `MODEL_CFG` 打印出来，并在启动前 `test -f "$MODEL_CFG"`。
3. 不要用“应该在 snapshot 里”当路径依据；仓库 config 和 HF checkpoint 是两类资产。

## 2026-05-19 — 测旧 PR 前先做 base commit venv/ABI smoke，别直接跑完整 profiling

**症状**：PR #3606 base commit 在 0.21.0 venv 下加载 HunyuanImage3 失败：`_hunyuan_image3_unpack_packed_topk() missing 1 required positional argument: 'num_experts'`。这不是 PR 性能回归，而是旧 base commit 与当前 vLLM / custom op ABI 不匹配。

**根因**：旧 PR 的 base commit 可能基于不同 vLLM-Omni/vLLM 组合；直接拿当前节点默认 venv 跑完整 e2e，会把环境不兼容误包装成 PR 失败。远端 `docs/remote_server.md` 里的 venv 表只能说明历史用途，不能替代本 PR base smoke。

**解法**：测旧 PR 顺序固定：
1. 读 PR 首 commit / base commit，确认年代和目标 vLLM 版本。
2. 对 base 和 patch 各建干净 worktree。
3. 先做 import/init smoke：
   ```bash
   PYTHONPATH=/home/wzr/wt-pr-base $VENV/bin/python - <<'PY'
   import vllm
   print("vllm", vllm.__version__)
   from vllm_omni.model_executor.models.hunyuan_image3.hunyuan_image3 import HunyuanImage3RotaryEmbedding
   print("import ok", HunyuanImage3RotaryEmbedding)
   PY
   ```
   对 HunyuanImage3 这类 custom op / MoE 路径，最小 `Omni(...).init` smoke 也要先跑；它通过后才跑 profiling/accuracy。

**怎么避免**：
1. 旧 PR 验证不能默认复用“当前 main 可用”的 venv；base commit 必须先 smoke。
2. `RuntimeWarning: vLLM and vLLM-Omni appear mismatched` 不能当普通噪音，后续任何 crash 都先按版本矩阵处理。
3. 完整 profiling 前先确认 base 能启动；base 不启动时，结论写“environment/base ABI blocker”，不要写性能收益。

## 2026-05-19 — 新终端远端冷启动太慢：不要把已有上下文重新 discover 一遍

**症状**：PR #3606 分支已经强推到 `bddc12a5a`，远端也已有 `/home/wzr/wt-pr3606-base` 和 `/home/wzr/wt-pr3606-patch` 两个现成 worktree。但新终端上来后先跑了大量探测命令（find repo、find venv、grep profiler、grep Omni、查 deploy yaml、查历史脚本等），中间还因为 PowerShell 管道 CRLF 误判文档路径不存在。最后才复用现成 base/patch 目录并启动 tmux 长跑测试。

**根因**：
- 新终端没有先消费当前会话/issue/PR 已知事实，把远端当全新机器重新侦察。
- 远端 SSH 单次往返很慢，19 条小命令比 1 个聚合 probe 脚本贵很多。
- PowerShell 直接管道到 `ssh bash -s` 时 CRLF/quoting 会制造假阴性，让“路径不存在”这类判断变脏。

**解法**：
1. 新终端接手前先写 5 行 runbook：目标 PR/branch/head、远端 worktree、venv、输出目录、当前长跑 tmux/session。
2. 如果已有 worktree / 脚本 / 输出目录，先 `git -C <dir> status` + `git -C <dir> rev-parse HEAD` 验证，不要 `find /home /root` 全盘扫。
3. discovery 必须聚合成一个无 BOM/LF 脚本，一次 SSH 返回完整事实；禁止 10+ 条一行 SSH 慢慢摸。
4. 用户/上个终端已经给出“PR branch 已强推到 <sha>”时，直接围绕这个 sha 同步，不要重新推导 branch 状态。

**怎么避免**：
1. 远端冷启动 checklist：
   ```text
   Known head: <sha>
   Known worktrees: <base>, <patch>
   Known venv: <venv>
   Known tmux/output: <session>, <out_dir>
   Next action: sync/check/run/poll
   ```
2. 任何“路径不存在”的结论都要先排除 CRLF/BOM/本地变量展开；用 `printf %q` / `ls -ld` / `test -d` 的聚合脚本确认。
3. 远端慢时优先复用现有目录和脚本；只有现有事实冲突时才扩大搜索范围。
