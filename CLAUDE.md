# vLLM-Omni × HunyuanImage-3.0-Instruct 工作目录

## CI / dummy guard verification rule

When adding or changing a CI test, dummy guard, smoke test, or PR-level watch test, `compileall` and `git diff --check` are not enough. The newly added or changed test function must be executed at least once.

If local pytest cannot start because dependencies such as `vllm` are missing, do not stop at syntax checks. Use an existing venv, the remote/container CI-like environment, or a minimal script that executes the same core test path. For dummy tests that use `object.__new__`, verify runtime behavior and do not assume attributes are writable; check for read-only properties and monkeypatch/stub them at the class level when needed.

If this cannot be executed, state the blocker explicitly and do not claim the guard is verified.

## ⚠️ 硬性规则（违反过多次，每次会话开头先读）

1. **远端发命令后，先短 sleep（≤5s）+ capture 确认脚本真启动了，才能长 sleep 等结果。**
   - 判据：capture 输出必须包含 pytest 的 `collected N items` / 明确的程序日志 / 明确的错误信息。光看到 shell 回显不算。
   - 违反过 2 次（2026-04-21），详见 `memory/user_prefs.md`。

2. **退 srun shell 前必须在容器里 `pkill -9 -f vllm_omni`。**
   - Slurm 和 docker 不通信，srun exit 不会杀容器内进程，漏做就占死 GPU + 同事投诉。
   - 详见 `memory/srun_exit_kill_container_procs.md`。

3. **容器内一切持久内容（模型、venv、缓存、代码）必须写到挂载的 Lustre 路径。**
   - 别写 `~/.cache` / `/tmp` / 容器层。HF 模型 `export HF_HOME=/home/models`。
   - 详见 `memory/no_container_ephemeral.md`。

4. **进新节点先看别人容器怎么挂，不要假设路径。**
   - `docker inspect <other_container>` 最权威，别信文档。
   - 详见 `memory/remote_node_general.md`。

5. **香港机器直连 PyPI，不要用清华源。**
   - 详见 `memory/remote_is_hongkong.md`。

6. **做"团队同款 CI"类需求，先打开 `tests/` 里现有文件看一眼。**
   - 别基于幻觉讨论方案。详见 `memory/always_inspect_existing_tests_first.md`。

7. **国策**：改 `pipeline_registry.py` 而不是 YAML；改 YAML 为 CLI；不引入新 JSON/YAML 启动配置文件。

8. **调试阶段禁止用 git commit-push-pull 循环。**
   - 调试 = 在远端直接写 `/tmp/test_xxx.py` 或 Python one-liner 快速试错。
   - 确认方案可行后，回本地写正式代码，**一次** commit-push-pull 部署。
   - 判据：如果你的 commit message 是 "fix attempt N"，说明你在用部署流程做调试，**立刻停下来换策略**。
   - 违反过 1 次（2026-04-21 tokenizer 修复 6 轮 git 循环，烧了一天 + $300），详见 `memory/feedback_remote_debug_strategy.md`。

9. **接入新模型/新组件前，必须先做环境侦察，禁止直接写代码。**
   - 一次 SSH 收集所有信息：config JSON 内容、目录文件列表、HF cache 结构（refs/ 是否存在）、关键包版本。
   - 读目标代码路径：从调用入口追到实际加载逻辑，看清楚会调什么 API。
   - 看同类模型怎么做的（GLM-Image / BAGEL 等先例）。
   - **侦察结果写到 tmux capture 或临时文件里留痕，再决定方案。**
   - 违反过 1 次（2026-04-21 没看 tokenizer_config.json 就写 AutoTokenizer 代码），详见 `memory/feedback_tokenizer_debug_retro.md`。

10. **tmux window 有前台进程时，不能往该 window 发 shell 命令。**
    - `python ... | tee` 占住 shell，send-keys 发的文本进了进程 stdin，不会被 shell 执行。
    - 测试 API / 跑脚本必须从**另一个 tmux window** 发。
    - 违反过 1 次（2026-04-21 往 serve 前台进程发 curl）。

11. **跨节点执行命令用脚本文件，禁止嵌套引号。**
    - `ssh nodeA "docker exec $(docker ps -q) ..."` 的 `$()` 会在本地展开 → 必错。
    - 正确做法：写脚本到共享文件系统（Lustre），然后 `ssh nodeA bash /shared/path/script.sh`。
    - 违反过 1 次（2026-04-21 docker exec 引号嵌套连续失败 3 次）。

12. **奥卡姆剃刀：先用最少资源/最简配置试，不够再加。**
    - 不要基于未验证的假设分配资源（"80B 模型肯定要 4 卡"）。
    - 先试最小配置（2 卡 TP=2），OOM 了再加卡，不要反过来。
    - 写 fixture / 配置时，硬编码的资源要求必须有实测依据，不能靠猜。
    - 违反过 1 次（2026-04-21 GEBench fixture 硬编码 4 卡，从未验证 2 卡是否够用，导致被 GPU 可用性卡住）。

13. **用户给出明确技术方案时，直接执行，禁止"先试试不改看行不行"。**
    - 用户比你更了解模型和硬件约束。用户说减层就减层，说 TP=2 就 TP=2。
    - 违反过 1 次（2026-04-21 用户说 TP=2+减层，我先试不减层 → OOM，浪费一轮远端调试），详见 `memory/feedback_follow_user_instruction.md`。

13. **优先最简单直接的方案，禁止绕远路。**
    - 现有环境有 venv 就 `source .venv/bin/activate`，不要 PYTHONPATH hack / pip install 升级系统包 / 加别名 patch。
    - 先检查现有环境是否已有需要的东西，有就直接用。
    - 违反过多次（2026-04-15 ~ 2026-04-16），详见 `memory/feedback_no_detours.md` + `memory/feedback_use_venv.md`。

14. **已知结论直接应用，禁止重新推导。**
    - 之前对话已经得出的结论（error book、memory、上一轮调试结果），直接用，不要重新验证。
    - 优先行动，减少分析循环。
    - 违反过至少 1 次（用户原话："为什么耗时那么久才分析出这种最简单的东西，这个之前不是已经发现过了么"），详见 `memory/user_prefs.md`。

15. **进容器后必须 `unset TRANSFORMERS_CACHE`，空字符串不行。**
    - 很多 Docker 镜像默认设了 `TRANSFORMERS_CACHE=/models/huggingface/transformers`，它会**覆盖** `HF_HOME`。
    - `TRANSFORMERS_CACHE=`（空字符串）≠ `unset`：空字符串仍被 `os.environ.get()` 返回，传给 `hf_hub_download` 后行为不可预测。
    - 进容器后先 `env | grep -i cache` 检查。
    - 违反过 1 次（2026-04-22 GEBench DiffusionWorker 找不到模型），详见 `memory/transformers_cache_gotcha.md`。

16. **写 accuracy test 时，所有 CLI 参数必须从 fixture 透传到 benchmark 主函数。**
    - 特别是 `--samples-per-type` / `--max-samples` 这类控制数据量的参数。
    - 漏传 = 跑全量数据集，smoke test 变成几小时的完整 benchmark。
    - 写完后 diff 对比同类测试（如 Qwen-Image 的 gebench test）确认参数齐全。
    - 违反过 1 次（2026-04-22 GEBench 跑了 15+ 分钟才发现没传 --samples-per-type）。

17. **离线环境（`HF_HUB_OFFLINE=1`）跑 accuracy test 前，确认所有模型都已下载。**
    - accuracy test 通常涉及 generate 模型 + judge 模型，两个都要在 HF cache 里。
    - checklist：`ls $HF_HOME/hub/ | grep models--` 确认 generate model、judge model、dataset 三项齐全。
    - 违反过 1 次（2026-04-22 generate 成功但 judge 模型没下载，evaluate 阶段直接失败）。

18. **跑任何远端脚本/accuracy test 前，必须过"启动前三连"。**
    - (1) GPU 空闲：`nvidia-smi --query-gpu=index,memory.used,memory.free --format=csv,noheader`
    - (2) 模型路径存在：`find $HF_HOME/hub -maxdepth 3 -name "snapshots" -type d`
    - (3) 缓存变量正确：`env | grep -iE "cache|hf_home|offline"`
    - kill 进程后必须 `sleep 5 + nvidia-smi` 确认显存归零再重启；有残留时 judge server 用 `gpu_memory_utilization=0.5`。
    - 违反过 1 次（2026-04-23 没做侦察直接跑，浪费 4 小时），详见 `.claude_errors/hunyuan_image3.md`。

19. **容器内跑 multiprocessing 命令前，先 `cd /tmp`。**
    - Python multiprocessing spawn 模式子进程会 `os.chdir()` 到父进程 cwd。如果 cwd 是 Lustre 权限受限目录（如 `/scratch/...`），子进程报 `PermissionError: [Errno 13]`。
    - 违反过 1 次（2026-04-23 vllm-omni diffusion executor 4 次 worker 全崩，查了 3 轮才发现是 cwd 权限问题）。

20. **释放远程资源必须三步走，缺一不可。**
    - (1) 容器内：`pkill -9 -f python && pkill -9 -f vllm_omni` 杀 GPU 进程
    - (2) 容器内：`exit` 退出 docker exec session
    - (3) 计算节点：`exit` 退出 srun shell，释放 Slurm job
    - 最后 `squeue -u <user>` 确认 job 列表为空。
    - 违反过 1 次（2026-04-23 用户说"释放资源"，只做了 pkill 没退容器和 srun，job 一直占着节点）。

21. **git commit 默认加 DCO sign-off。**
    - 所有 commit 必须带 `--signoff`（即 `-s`），生成 `Signed-off-by: Name <email>` 行。
    - vllm-omni 上游要求 DCO，缺 sign-off 的 commit 会被 CI 拒绝。

22. **开发在 git worktree 里做，主仓库工作区保持干净。**
    - 每个 PR / 大功能 / 实验探索 → 一个 worktree，命名 `wt-<purpose>`。
    - 主仓库目录只作 hub，不直接写代码。
    - 起 worktree：`git worktree add ../wt-feature-xxx feature/xxx`；完事 `git worktree remove ../wt-feature-xxx`。
    - 违反过 1 次：在主分支多 PR 上下文混跑导致 squash 时旧分支夹带货洗不干净，烧了一天。

---

## 目录布局

```
workflow-starter/
├── CLAUDE.md                # 本文件（22 条硬规则 + 索引）
├── README.md                # 怎么用：4 步 setup + 飞轮机制说明
├── .gitignore               # 排除密码/凭证/临时文件
├── 拉起claude.bat           # 快速启动 Claude Code（跳过权限确认）
├── 启动官方claude.bat       # 带代理启动 Claude Code
├── docs/
│   ├── architecture.md      # 核心架构、代码地图、命名约定、雷区
│   └── remote_server.md     # 远端 GPU 服务器连接指南（脱敏版）
├── memory/                  # 项目记忆（跨会话持久化，18 篇 frontmatter MD）
├── .claude/                 # Claude Code 配置
│   ├── settings.json        # Stop hook 注册
│   ├── commands/            # lastwords.md + 遗言.md（会话交接 slash command）
│   └── hooks/
│       └── stop-gate.sh     # 数据飞轮门禁 hook
├── .claude_errors/          # Error book（踩坑记录，6 篇）
└── skills/                  # Custom skills（claudeception / clean-thinking / reflect-system）
```

## 快速索引

| 主题 | 文件 | 说明 |
|------|------|------|
| 架构 & 代码地图 | [docs/architecture.md](docs/architecture.md) | vLLM-Omni 架构、代码地图、命名约定、雷区 |
| 远端服务器 | [docs/remote_server.md](docs/remote_server.md) | SSH 连接、Slurm 申请、tmux 操作模板 |
| Error Book | [.claude_errors/hunyuan_image3.md](.claude_errors/hunyuan_image3.md) | 踩坑记录，进入任何 phase 前先读 |

## 可用 Skills（`vllm-omni/.claude/skills/`）

仓库内置的接入工程模板，由 Claude Code 自动加载。**何时主动调用**：

| Skill | 触发条件（命中即用 Skill 工具调用，名字一致） | 当前项目相关性 |
|-------|------------------------------------------------|----------------|
| `add-diffusion-model` | 接入 HunyuanImage3 的 **DiT 部分** / 新增任何 diffusion 模型 / 改 `vllm_omni/diffusion/models/` 下的 pipeline 或 transformer / 加 TP・SP(USP)・CFG-Parallel・HSDP・Cache-DiT・CPU offload / 注册 `_DIFFUSION_MODELS` | **高**——HunyuanImage3 走 Path B（custom repo + bypass loader），BAGEL 是直接参考样例 |
| `add-tts-model` | 新增 TTS 模型 / 接 `serving_speech.py` / async chunk 流式 / 给 AR 热环加 CUDA graph | 目前无（HunyuanImage3 是 image，不是 audio）。**例外**：将来给 AR decode 加 CUDA graph 提速时可参考 Phase 5 |
| `vllm-omni-npu-upgrade` | 把 GPU runner 的 omni 改动同步到 NPU runner / 升级 vllm-ascend 对齐 | 目前无（GPU 工作流，不碰 NPU）。**附带价值**：grep `Omni-new` 注释块可以快速定位 `gpu_*_model_runner.py` 里 vllm-omni 在 vllm 上加的改动 |

**调用方式**：用 `Skill` 工具，`skill` 字段填名字（如 `add-diffusion-model`）。**不要**和 `CLAUDE.md` 里的硬规则、`memory/`、`.claude_errors/` 冲突——skill 是"怎么写代码 fit 进框架"，硬规则是"怎么不踩远端/容器/调试的坑"，两者互补。

**另外**：`claudeception` skill 负责数据飞轮自动积累——从会话提炼踩坑记录到 `.claude_errors/`、常识到 `memory/`，条目过多时自动按主题拆分。调用 `/claudeception` 或在 stop-gate hook 提示时触发。

## 项目记忆（`memory/`）

跨会话持久化知识，每个文件一个主题，带 frontmatter 元数据。

| 文件 | 描述 |
|------|------|
| [remote_node_general.md](memory/remote_node_general.md) | **进入陌生远端节点的通用流程**（别假设路径，先看别人容器怎么挂） |
| [no_container_ephemeral.md](memory/no_container_ephemeral.md) | **规则：永远写宿主挂载路径，不写容器临时路径**（HF_HOME / pip cache 等） |
| [srun_exit_kill_container_procs.md](memory/srun_exit_kill_container_procs.md) | **规则：退 srun 前必须清容器里的进程**（Slurm 管不了 docker 内进程，漏做占死 80GB 卡） |
| [ar_dit_bridge.md](memory/ar_dit_bridge.md) | AR→DiT 数据桥接：需传 cot_text 而非 raw token IDs |
| [bidirectional_attention.md](memory/bidirectional_attention.md) | 图像 token 双向注意力：需加 `is_mm_prefix_lm` |
| [version_compat.md](memory/version_compat.md) | 远端 vllm/numpy/cv2 版本兼容问题 |
| [user_prefs.md](memory/user_prefs.md) | 用户协作偏好 |
| [ci_gitignore_json.md](memory/ci_gitignore_json.md) | .gitignore 有 `*.json`，新增 JSON test config 必须 `git add -f` |
| [feedback_no_detours.md](memory/feedback_no_detours.md) | 优先最简单直接的方案，不要绕远路 |
| [always_inspect_existing_tests_first.md](memory/always_inspect_existing_tests_first.md) | 做 CI 类需求先看 tests/ 现有文件 |
| [docker_exec_cwd_workaround.md](memory/docker_exec_cwd_workaround.md) | docker exec 报 chdir permission denied 的 workaround |
| [remote_is_hongkong.md](memory/remote_is_hongkong.md) | 香港机器直连 PyPI，不要用清华源 |
| [auto_push_pr_branches.md](memory/auto_push_pr_branches.md) | PR 分支改完自动 push，不等用户说 |
| [transformers_cache_gotcha.md](memory/transformers_cache_gotcha.md) | TRANSFORMERS_CACHE 覆盖 HF_HOME 陷阱，必须 unset |
| [feedback_follow_user_instruction.md](memory/feedback_follow_user_instruction.md) | 用户给出明确方案时直接执行 |
| [feedback_remote_debug_strategy.md](memory/feedback_remote_debug_strategy.md) | 远端调试不走 git 循环，先在远端快速试错 |
| [feedback_tokenizer_debug_retro.md](memory/feedback_tokenizer_debug_retro.md) | 先侦察再写代码，HF cache 结构备忘 |
| [feedback_use_venv.md](memory/feedback_use_venv.md) | 远端用 source .venv/bin/activate，不用 PYTHONPATH hack |

## 包管理

- 远端容器内安装包一律用 `uv pip install`，不要用原生 `pip install`
- uv 在 Lustre 挂载目录下会报 `uv.toml` permission denied，需先 `cd /tmp` 再执行

## Error Book 格式

任何新踩的坑按主题追加到 `.claude_errors/<topic>.md`（如 `git_and_rebase.md`、`docker_and_container.md`）：

```markdown
## YYYY-MM-DD HH:MM — <一句话标题>
**症状**：<报错/不符合预期的具体表现>
**根因**：<分析后的真正原因>
**解法**：<怎么修的>
**对未来的提醒**：<下一次怎么避免>
```
