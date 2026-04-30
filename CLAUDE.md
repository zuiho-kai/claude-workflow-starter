# vLLM-Omni × HunyuanImage-3.0-Instruct 工作目录

本文件是**索引**，不放细节。每条硬规则只有一句钩子 + 跳转链接，rationale 全在 `memory/` 和 `.claude_errors/`，命中场景再点进去看。

**怎么用**：
- 会话开头扫一遍下面的「硬性规则」
- 进新场景前先看 [memory/MEMORY.md](memory/MEMORY.md) 找对应主题目录
- 踩新坑追加到 `.claude_errors/<topic>.md`（格式见末尾）

---

## ⚠️ 硬性规则（违反过多次，按场景分组）

### A. 远端 / 容器 / Slurm
- **A1** 远端发命令后先短 sleep（≤5s）+ capture 确认脚本真启动（看到 `collected N items` / 程序日志），再长 sleep 等结果 → [user_prefs](memory/feedback/user_prefs.md)
- **A2** 退 srun 前必须容器内 `pkill -9 -f vllm_omni`，否则占死 GPU → [srun_exit_kill_container_procs](memory/remote/srun_exit_kill_container_procs.md)
- **A3** 容器内一切持久内容（模型、venv、缓存、代码）必须写宿主挂载路径，别写 `~/.cache` / `/tmp` / 容器层 → [no_container_ephemeral](memory/remote/no_container_ephemeral.md)
- **A4** 进新节点先 `docker inspect <other_container>` 看挂载，别信文档别假设路径 → [remote_node_general](memory/remote/remote_node_general.md)
- **A5** 香港机器直连 PyPI，不要用清华源 → [remote_is_hongkong](memory/remote/remote_is_hongkong.md)
- **A6** tmux window 有前台进程时不能往该 window 发 shell 命令（send-keys 进了进程 stdin），从另一个 window 发
- **A7** 跨节点执行命令用脚本文件，禁止嵌套引号（`ssh nodeA "docker exec $(...) ..."` 的 `$()` 在本地展开必错）
- **A8** 进容器后必须 `unset TRANSFORMERS_CACHE`，空字符串 ≠ unset → [transformers_cache_gotcha](memory/remote/transformers_cache_gotcha.md)
- **A9** 容器内跑 multiprocessing 前 `cd /tmp`，避免 spawn 子进程 chdir 到 Lustre 受限路径报 `PermissionError` → [docker_exec_cwd_workaround](memory/remote/docker_exec_cwd_workaround.md)
- **A10** 释放资源三步走：容器内 pkill → exit docker exec → exit srun，最后 `squeue -u <user>` 确认空 → [srun_exit_kill_container_procs](memory/remote/srun_exit_kill_container_procs.md)

### B. 调试方法论
- **B1** 调试阶段禁止 git commit-push-pull 循环；远端直接写 `/tmp/test_xxx.py` 试错；commit message 出现 "fix attempt N" 立刻停 → [feedback_remote_debug_strategy](memory/feedback/feedback_remote_debug_strategy.md)
- **B2** 接入新模型前先做环境侦察：config JSON / 目录列表 / HF cache 结构 / 包版本 / 同类先例（GLM-Image / BAGEL），结果留痕 → [feedback_tokenizer_debug_retro](memory/feedback/feedback_tokenizer_debug_retro.md)
- **B3** 奥卡姆剃刀：先用最少资源最简配置试（2 卡 TP=2 试，OOM 再加），硬编码资源要求必须有实测依据
- **B4** 用户给出明确技术方案时直接执行，禁止"先试试不改看行不行"——用户比你更了解模型和硬件 → [feedback_follow_user_instruction](memory/feedback/feedback_follow_user_instruction.md)
- **B5** 优先最简单直接的方案，禁止绕远路（venv 优先于 PYTHONPATH hack / pip 升级系统包） → [feedback_no_detours](memory/feedback/feedback_no_detours.md) + [feedback_use_venv](memory/feedback/feedback_use_venv.md)
- **B6** 已知结论（error book / memory / 上轮调试结果）直接应用，禁止重新推导 → [user_prefs](memory/feedback/user_prefs.md)
- **B7** 测 HF 模型 baseline 前必先 `grep -E "demo|generate_image|prepare_model_inputs" $REPO/README.md` 找官方 API；禁止自己拍参数替代 `model.generate_image()` → [feedback_check_official_demo_first](memory/feedback/feedback_check_official_demo_first.md)

### C. CI / 测试
- **C1** 做"团队同款 CI"先打开 `tests/` 现有文件看一眼，别基于幻觉讨论方案 → [always_inspect_existing_tests_first](memory/ci/always_inspect_existing_tests_first.md)
- **C2** 写 accuracy test 时所有 CLI 参数必须从 fixture 透传到 benchmark（`--samples-per-type` / `--max-samples` 漏传 = 跑全量数据集，smoke 变几小时）
- **C3** 离线环境（`HF_HUB_OFFLINE=1`）跑 accuracy test 前 checklist：generate model / judge model / dataset 三项齐全 `ls $HF_HOME/hub/ | grep models--`
- **C4** 跑任何远端脚本前过「启动前三连」：(1) GPU 空闲 (2) 模型路径存在 (3) 缓存变量正确；kill 进程后必 `sleep 5 + nvidia-smi` 确认显存归零

### D. Git / PR
- **D1** git commit 默认加 DCO sign-off（`-s`），缺 sign-off 上游 CI 拒绝
- **D2** 开发在 git worktree 里做，主仓库工作区保持干净；命名 `wt-<purpose>`，完事 `git worktree remove`
- **D3** 开 PR 前 + cherry-pick/rebase 后必跑 `git log --oneline origin/main..HEAD | nl` 逐条查污染；`git diff --stat` 改的文件应跟 PR 主题强相关，无关文件 >1-2 个就要查 → [.claude_errors/git_and_pr_branch_pollution](.claude_errors/git_and_pr_branch_pollution.md)

### E. 架构国策
- **E1** 改 `pipeline_registry.py` 而不是 YAML；改 YAML 为 CLI；不引入新 JSON/YAML 启动配置文件

---

## CI / dummy guard verification rule

When adding or changing a CI test, dummy guard, smoke test, or PR-level watch test, `compileall` and `git diff --check` are not enough. The newly added or changed test function must be executed at least once.

If local pytest cannot start because dependencies such as `vllm` are missing, do not stop at syntax checks. Use an existing venv, the remote/container CI-like environment, or a minimal script that executes the same core test path. For dummy tests that use `object.__new__`, verify runtime behavior and do not assume attributes are writable; check for read-only properties and monkeypatch/stub them at the class level when needed.

If this cannot be executed, state the blocker explicitly and do not claim the guard is verified.

---

## 目录布局

```
workflow-starter/
├── CLAUDE.md                # 本文件（索引）
├── README.md                # 怎么用：4 步 setup + 飞轮机制
├── docs/
│   ├── architecture.md      # 核心架构、代码地图、命名约定、雷区
│   └── remote_server.template.md  # 远端连接模板（首次复制为 remote_server.md）
├── memory/                  # 项目记忆（按主题分子目录，见 MEMORY.md）
├── .claude_errors/          # Error book（按主题分文件）
├── .claude/                 # Stop hook + slash commands + skills
└── 拉起claude.bat / 启动官方claude.bat
```

## 快速索引

| 主题 | 文件 |
|------|------|
| 架构 & 代码地图 | [docs/architecture.md](docs/architecture.md) |
| 远端服务器 | [docs/remote_server.md](docs/remote_server.md)（首次由模板生成） |
| 项目记忆总入口 | [memory/MEMORY.md](memory/MEMORY.md) |
| Error Book | [.claude_errors/](.claude_errors/) |

## 可用 Skills

仓库内置接入工程模板（`vllm-omni/.claude/skills/`），按需用 `Skill` 工具调用：

| Skill | 何时调用 | 当前项目相关性 |
|-------|---------|----------------|
| `add-diffusion-model` | 接 HunyuanImage3 DiT / 改 `vllm_omni/diffusion/models/` / 加 TP・SP・CFG-Parallel 等 | **高** |
| `add-tts-model` | 新增 TTS / 改 `serving_speech.py` / async chunk 流式 / AR CUDA graph | 目前无（image，非 audio） |
| `vllm-omni-npu-upgrade` | 同步 GPU runner omni 改动到 NPU runner | 目前无（不碰 NPU） |

`claudeception` skill 负责数据飞轮自动积累——从会话提炼踩坑到 `.claude_errors/`、常识到 `memory/`，stop-gate hook 触发或 `/claudeception` 调用。

## 远端实验自动初始化

含真实凭证的配置文件全部走「template + gitignore」模式——仓库里只有 `*.template.md`（占位符版本），实例文件已 `.gitignore`，cc 进新会话时检查实例是否存在，不存在就从 template 复制并问用户填。

| Template（仓库） | 实例（gitignored） | 何时引导用户填 |
|------------------|--------------------|----------------|
| `docs/remote_server.template.md` | `docs/remote_server.md` | 第一次需要 SSH 到远端时 |
| `memory/remote/ssh_connection_pattern.template.md` | `memory/remote/ssh_connection_pattern.md` | 第一次需要 ASKPASS 自动化 SSH 时 |
| `memory/remote/remote_test_env.template.md` | `memory/remote/remote_test_env.md` | 第一次提到「主测试节点」时 |
| `memory/remote/remote_0036_env.template.md` | `memory/remote/remote_<NODE_TAG>_env.md` | 进每个新计算节点时各填一份 |

**cc 行为约定**：发现某个 template 在仓库里、但对应实例 `.md` 不存在时，主动 `cp` 一份并问用户：「这个文件需要填以下信息：…，要现在填吗？」。已存在则直接读。

填好的实例文件不会被 commit（`.gitignore` 已覆盖），但本机持久保留，下次会话不会再问。

## 包管理

- 远端容器内一律 `uv pip install`，不要原生 `pip install`
- uv 在 Lustre 挂载目录下报 `uv.toml` permission denied，先 `cd /tmp` 再执行

## Error Book 格式

按主题追加到 `.claude_errors/<topic>.md`（如 `git_and_rebase.md`、`docker_and_container.md`）：

```markdown
## YYYY-MM-DD HH:MM — <一句话标题>
**症状**：<报错/不符合预期的具体表现>
**根因**：<分析后的真正原因>
**解法**：<怎么修的>
**对未来的提醒**：<下一次怎么避免>
```
