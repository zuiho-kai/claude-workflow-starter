# Error Book: 远端环境 & SSH

## 2026-05-19 — 小 lint 修复不该默认上远端复验
**症状**：CI 报 `ruff check` 未使用变量，本地删除变量后已经跑过覆盖改动文件的 `ruff check` 和 `py_compile`，但又默认 SSH 到远端复验，结果远端 venv 缺 ruff binary，白白引入环境噪音。
**根因**：把"远端验证流程要规范"（A12）误用成"任何修复都必须远端验证"。这次问题是纯静态 lint，小范围一行删除，本地 ruff 已经命中同一个检查；远端不提供额外信号，反而增加 venv/tooling 变量。
**解法**：小范围 lint/static 修复：本地跑对应 hook/ruff + 必要语法检查即可；只有本地缺依赖、GPU/e2e、远端环境相关、或用户明确要求时才上远端。
**对未来的提醒**：验证要匹配风险来源。代码行为/GPU/环境问题用远端；格式、未使用变量、PR 文档、纯文本规则更新优先本地闭环。不要用"多跑远端"伪装严谨。

## 2026-04-21 — 假设路径 + HF 缓存丢失
**症状**：docker exec 失败、挂载路径为空、HF 缓存消失
**根因**：不同节点布局不同；容器内 `~` 在容器层，非持久
**侦察三连**：
```bash
docker ps && docker inspect <container> --format '{{range .Mounts}}...'
find /home /scratch -maxdepth 5 -name "snapshots" -type d 2>/dev/null
env | grep -iE "cache|hf_home"
```
**提醒**：建容器挂持久存储，`HF_HOME` 指向持久路径

## 2026-04-22 — TRANSFORMERS_CACHE 覆盖 HF_HOME
**症状**：模型路径指向错误的 transformers cache 目录而非 `$HF_HOME/hub/`
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
**根因**：Windows Git Bash / OpenSSH ControlMaster 均不支持；ASKPASS 失败触发 fail2ban
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

## 2026-04-27 — 远端命令盲等不看日志
**症状**：启动 server 后用 `while ! curl health; sleep 5; done` 循环等待，长时间内没有任何输出给用户
**根因**：违反硬规则 A1——远端发命令后必须先短 sleep（≤5s）+ capture 确认启动了
**解法**：后台启动（`nohup ... &`），5s 后 `tail -20` 日志确认无错，再周期检查
**对未来的提醒**：禁止紧密 poll 循环阻塞 SSH 隐藏输出；每次检查必须打印日志片段

## 2026-05-14 — cp -r 复制别人的 venv 想"独立"反而踩坑
**症状**：用户要求"new own venv"，没用 `uv venv` 而是 `cp -r $DATA_DIR/venv .venv`，源 venv 复制后异常膨胀且 `bin/python` 未生成
**根因**：venv 是 "site-packages 指针 + wheel 安装记录" 的元数据集合，不是普通目录。cp 行为受 symlink / uv cache / 并行 fs 语义影响。更根本的——复制后仍然不是"own"，只是别人 venv 状态的 fork。用户的"new owner venv"字面就是 `uv venv` 从零建一个
**解法**：永远走 `uv venv .venv --python <python>` 新建
**对未来的提醒**：(1) 看到 "new"/"own"/"独立 venv" → 自动 `uv venv` 不要找捷径；(2) `du -sh source` vs `du -sh dest` 差异 >1.5x → 立刻停手反问"是不是走错路"

## 2026-05-18 — 跨主机同步代码用 patch/scp 走弯路，git push/fetch 才是正路
**症状**：本地改完代码想同步到远端 worktree，先试 `git diff | ssh apply -`（上下文不匹配失败）、再想 scp，最后才用 git commit + push + 远端 `git fetch + git checkout` 才稳定
**根因**：纠结于"调试期不要 commit-push 循环"（B1）而绕远路。但 B1 管的是"fix attempt N"型的本地循环；**跨主机同步代码**本来就只有 git 这一条正路
**解法**：跨主机同步用 git commit + push to fork branch + remote git fetch + git checkout FETCH_HEAD。`git diff | ssh apply` 在 line ending / 文件未保存 / context 漂移时必跪
**怎么避免**：B1 边界：单机本地试错走 `/tmp/test_xxx.py`；跨主机同步走 commit-push-fetch，禁用 patch/scp

## 2026-05-19 — PowerShell 到 SSH 投递脚本：变量展开 / 空文件 / BOM 三连坑
**症状**：通过 PowerShell heredoc 投递远端脚本，远端脚本变成 0 字节；另一次脚本首行带 UTF-8 BOM，远端报 `No such file or directory`；还出现过 `$VENV` 被本地 PowerShell 展开，导致远端脚本拿不到期望变量
**根因**：PowerShell 双引号 / here-string 会在本地先展开 `$VENV`、`$()` 等内容；Windows 写文本默认可能带 BOM；bash 把 BOM 当作 shebang 前的不可见字符
**解法**：复杂远端脚本优先本地生成无 BOM 文件，或用单引号 here-string，并在远端落盘后立刻检查 `wc -c` + `sed -n '1,40p'` + `bash -n`；后台启动后必须短 sleep + tail 日志确认已进入程序日志
**怎么避免**：(1) PowerShell→SSH→bash 链路中任何 `$VAR` 都默认有本地展开风险，能单引号就单引号；(2) 远端脚本启动前固定三连：`wc -c`、`sed -n '1,40p'`、`bash -n`；(3) 看到日志 0 字节或没有程序首行 marker，先修脚本投递

## 2026-05-19 — 新终端远端冷启动太慢：不要把已有上下文重新 discover 一遍
**症状**：远端已有现成 worktree，但新终端上来后先跑了大量探测命令，最后才复用现成目录并启动长跑测试
**根因**：新终端没有先消费当前会话/issue/PR 已知事实，把远端当全新机器重新侦察。远端 SSH 单次往返很慢，多条小命令比 1 个聚合 probe 脚本贵很多
**解法**：新终端接手前先写 5 行 runbook：目标 PR/branch/head、远端 worktree、venv、输出目录、当前长跑 tmux/session。如果已有 worktree，先 `git -C <dir> status` + `git -C <dir> rev-parse HEAD` 验证，不要全盘扫
**怎么避免**：远端冷启动 checklist：Known head / Known worktrees / Known venv / Known tmux/output / Next action。discovery 必须聚合成一个无 BOM/LF 脚本，一次 SSH 返回完整事实；禁止 10+ 条一行 SSH 慢慢摸
