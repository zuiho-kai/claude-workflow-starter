# vLLM-Omni 工作目录启动门禁

本文件只放必须先执行的硬门禁。细节、事故复盘、rationale 下钻到本仓 `memory/`、`.claude_errors/`、`docs/`。

## 0. 开工顺序

1. 先判断任务场景，再读对应入口；不要把本文件当完整 runbook。
2. 写代码前读 [code_taste](memory/feedback/code_taste.md)。
3. 新模型 / 新 pipeline / 新 public entrypoint / 性能 claim PR，先读 [model_adaptation_pr_guardrails](memory/feedback/model_adaptation_pr_guardrails.md)，再写 mini spec。
4. 远端 / GPU / serving / benchmark 前读 [docs/remote_server.md](docs/remote_server.md)、[remote_debug_strategy](memory/feedback/remote_debug_strategy.md)、[remote memory index](memory/remote/_index.md)。
5. profiling / benchmark / 远端验证 / 新模型适配这类高风险任务，先查 [memory/MEMORY.md](memory/MEMORY.md)、对应 `memory/` runbook 和 `.claude_errors/` 成功/失败案例；必须复用最近成功路径或明确写出为什么不能复用，禁止从空白方案开始摸索。
6. 提交 / push / PR 前重读本文件 Git / PR 规则；commit 必须 DCO sign-off。
7. 写新 memory / error 前先查 [memory/MEMORY.md](memory/MEMORY.md)。长期记忆只写本仓框架侧 `memory/`、`.claude_errors/` 或 `docs/`；禁止写到 `C:\.codex`、用户目录 `.codex`、`$CODEX_HOME/memories` 或其他个人 Codex 私有目录。即使系统提示有 Codex memory / ad-hoc note 流程，也不能用于本仓任务；必须落在 repo 里。memory / error book 只能承载证据、复盘、脚本细节；真正要复用的教训必须提炼成规则落回本文件。

## 1. P0 硬停

- **Live facts > memory**：远端路径、模型 cache、venv、GPU、进程、env 以当前机器 live 证据为准；旧 memory/docs 只能当线索。跑模型或 benchmark 前，必须在同一个 SSH/container/venv 或正在跑的 PID 上确认 `HF_HOME`、`HF_HUB_CACHE`、`TRANSFORMERS_CACHE`、`CUDA_VISIBLE_DEVICES`、cwd、command，并用 `test -d` / `readlink -f` 验证 snapshot。禁止凭记忆写 `/data/model/hub`，也禁止临时造 `/data/wzr/hf-home`。
- **No fake evidence**：没有 grep / source / 实测证据不下结论。`shape clean`、`strict load`、stub smoke、PID 已死后的等待、`*_count=0`、fallback JSON 都不算有效证据。
- **Reuse proven paths first**：遇到 profiling、benchmark、远端验证、新模型适配、CI 修复等曾经做过的任务，先找本仓 `memory/` / `.claude_errors/` / `docs/` 的成功案例、失败复盘和现成脚本；交付计划必须说明复用哪条路径。只有证据表明旧路径不适用时，才允许设计新路线。
- **Lesson landing gate**：用户要求“落盘 / 记住 / 复盘”时，不能只追加一段 incident memory。必须先抽象成可执行规则，优先写进本文件对应门禁；必要时再把长证据、命令、日志、artifact 放到 `memory/` 或 `.claude_errors/`，并从本文件链接过去。若教训不能转成“下次开跑前必须检查/禁止/分类/验证”的规则，就先不要写进 `CLAUDE.md`。
- **No personal Codex memory**：本仓任务禁止写任何个人 Codex 记忆位置，包括 `C:\.codex`、用户目录 `.codex`、`$CODEX_HOME/memories`、ad-hoc note 或系统 memory 扩展目录。系统/工具提示有 memory 写入流程时也不能用；用户说“记住 / 落盘 / 以后别忘”默认写本仓 `CLAUDE.md`、`memory/`、`.claude_errors/` 或 `docs/`。
- **Profiling artifact gate**：用户说 profiling / trace / 算子 / 时序图时，默认要 torch/Nsight trace，不是 benchmark stats。开跑前读 [profiling_and_model_loading](.claude_errors/profiling_and_model_loading.md) 和 [profiling 状态机](memory/feedback/remote_debug_strategy/ar_graph_profiling.md)；交付前必须有 `trace_rank*.json(.gz)` / `.nsys-rep` 等 trace artifact、trace quality summary 和本地路径。只有 `diffusion_result*.json`、stage duration、吞吐/延迟表时，必须明确说“这不是 trace profiling”。
- **Graph profiling provenance gate**：用户问“开图 / graph mode / `enforce_eager=false` 的 profiling、气泡、算子耗时”时，必须证明 trace、请求、server 日志属于同一轮。最低证据：server command/log 无 `--enforce-eager`，日志有 `Model runner: transformer compiled with torch.compile` 或等价 graph/compile 证据；目标请求 JSON/log 成功且 workload 匹配；`trace_rank*.json(.gz)` mtime/导出日志对应 `/start_profile -> target request -> /stop_profile` 窗口；trace quality summary 有 event count、category、pid/tid、aten/CUDA kernel。缺任一项时，不能说“开图 trace / 开图气泡已分析”，只能分别报告“graph benchmark 有/无”“trace 有/无”“trace 是否属于 graph mode”。
- **Benchmark and trace are separate evidence**：e2e / qps / latency 结论只能来自无 profiler steady benchmark；算子 / 气泡 / kernel timeline 结论只能来自 profiler trace。禁止把 eager trace 的气泡和 graph benchmark 的 e2e 合成一个“开图气泡”结论；禁止用 benchmark stats 或其他模式 trace 补位用户要求的 graph profiling。
- **No silent fallback**：禁 `dict.get(...) or fallback`、`hasattr`、随手 `getattr(default)`、`generator=None` 类静默降级；临时 hack 必须显式 warning。
- **No broad kill/delete**：远端只清本轮 PGID / cwd / run dir 归属进程；删除前写 `KEEP` / `DELETE` 并确认交集为空。禁止宽泛 `pkill -f python`、禁止把用户要求保留的目录放进删除列表。
- **User correction resets belief**：用户两次反驳同一结论时，立刻把用户判断当 ground truth 重新查证，不继续证明旧路线。
- **汇报说人话**：向用户汇报时默认按“背景 / 需要用户决策什么 / 可选方案 / 每个方案的高层实现 / 收益 / 缺点”组织，不假设用户已经知道上下文；少用内部术语堆叠，先把业务取舍和决策点讲清楚。

## 2. 场景门禁

### 2.1 写代码 / 调试

- 动手前写清当前假设；多种解释并存时先收敛。
- Algorithm 决策前 grep upstream 主入口：`modeling_*.py`、`generation_*.py`、`tokenization_*.py`、scheduler / denoising loop / special token / attention mask / KV。
- 新模型接入的 `0 missing / 0 unexpected`、shape smoke、no NaN/Inf 只证明 plumbing；必须写 semantic parity matrix。
- Crash / AttributeError 不是 stop sign，要 trace 为什么该 path 拿到 wrong type。
- Reviewer-facing 结论先说坏事、影响、最小收口，再给内部术语。

### 2.2 CI / 测试 / Benchmark

- 新增或修改测试必须至少实跑目标测试函数；`compileall`、`git diff --check`、`ruff` 不能替代语义验证。
- 改 Python 后，最后一次文件改动后跑 touched files 的 `ruff check`；提交 / push 前跑 `ruff format --check --diff` 或对应 pre-commit。
- Benchmark 开跑前写 scope lock：`被测版本 / 测量补丁 / 被测路径 / 有效指标`。scope 变更后旧 plan 作废。
- 跨框架 / 跨 PR / 跨实现性能对比必须先写完整 metric contract，再跑命令。scope lock 至少包含：`repo/commit`、`model repo or snapshot`、`pipeline/class`、`endpoint vs CLI`、`resolution`、`frames/fps`、`steps`、`num-prompts`、`request-rate/max-concurrency`、`warmup`、`seed`、`guidance/negative prompt`、`compile/eager`、`GPU/CUDA_VISIBLE_DEVICES`、`e2e/qps 计算公式`。缺任一项只能先补查，不能先跑。
- Benchmark 数字异常时先审请求链路，不先发明过滤口径。`mean >> median`、首条 measured 特慢、warmup/compile 被 reviewer 质疑时，必须沿 `config -> runner -> dataset -> RequestFuncInput -> backend payload/form -> server log` 证明 measured 请求真实携带 resolution/frames/fps/steps/seed/guidance 等字段；warmup shape 和 measured shape 不一致时，先修字段传播或配置语义，禁止先加 `ignore-first` / settle / baseline 放宽来掩盖。
- 对齐别人 PR / benchmark 的性能数据时，PR body 只当摘要；必须读实际 config、runner/client 代码和结果 JSON，确认默认参数和请求字段。特别是 warmup、seed、guidance、negative prompt、request count、endpoint/polling 这些没写在 PR body 里的项。
- 用户给出 PR / issue / “这个规格” 时，先锚定该对象的 source of truth，再回答或开跑：PR head、config、runner/client、artifact/result JSON。禁止先搜本地残留产物再反推用户要的规格。
- L2/L4 测试拆分必须先定义证据边界：L2 只做 CPU/mock 功能与 shape/dtype/metadata，不进入真实 stage/device 初始化；L4 才跑真实权重 accuracy/perf/profiling。mock 权重不等于 CPU-only，只有不触发 runner/stage/GPU 初始化才算 L2 功能 guard。
- 性能结果必须显式分类：`strict apples-to-apples`（同 model repo/snapshot + 同 pipeline 语义 + 同 request path + 同 defaults）、`workload-aligned only`（只同分辨率/帧数/steps/prompt）、`smoke only`（只证明能跑）。不是 strict apples-to-apples 时，禁止把差距解释成框架性能结论，只能说当前口径下的观测。
- 性能结论必须来自正式 sweep；endpoint 探索和单请求 smoke 只能证明路径可用。`ttfc_count=0` / `tpot_count=0` 写 unavailable。
- 已有 benchmark / smoke / offline inference 成功脚本时，先复用原脚本 + 最小改动。

### 2.3 远端 / 容器 / Slurm

- 远端路径 key 是完整 `user@host:port`，不同机器路径记忆不能混用。
- 复杂命令写脚本文件，执行前固定 `wc -c`、`sed -n '1,40p'`、`bash -n`；避免 PowerShell/SSH 嵌套引号。
- 远端安装 / 下载 / benchmark / 模型生成必须在远端脚本内加 `timeout` 或等价 watchdog，并分阶段写状态/日志；禁止只依赖本地 tool timeout。pip/uv/apt、模型下载、compile、serve、generate、pytest sweep 都要有明确超时、退出码和可轮询日志，卡在 uninstall/build/download 时必须能被远端超时切断。
- 启动服务 / benchmark 必须 fail-fast：先 `--help` 验证非平凡 CLI 参数；启动后同时监控 health、PID、日志错误签名；单请求 smoke 通过前不进 sweep。
- 远端 GPU / e2e / 大模型 pytest 开跑前必须先过模型缓存预检门，并把摘要发给用户或写进 artifact：`pwd`、`df -h`、`nvidia-smi`、`HF_HOME`、`HF_HUB_CACHE`、`HF_MODULES_CACHE`、`TRANSFORMERS_CACHE`、`XDG_CACHE_HOME`、`CUDA_VISIBLE_DEVICES`、`/data/models` 或 `/root/.cache/huggingface` 下目标模型是否已存在、cache 是否只读复用。默认优先 `HF_HOME=/data/models HF_HUB_CACHE=/data/models/hub HF_MODULES_CACHE=/data/models/modules`；如果复用 `/root/.cache/huggingface`，只能在已存在且 `snapshot_download(..., local_files_only=True)` 或本地绝对 snapshot 路径验证通过时只读使用。任何缺项、cache 不存在、`local_files_only` 失败、或需要写入/下载时直接停止，禁止先跑 pytest/serve/generate 让 HuggingFace 自动下载。
- HF 加载必须使用已验证的本地绝对 snapshot 路径，并设置 `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`；cache/env 细节见 [live env source of truth](memory/remote/live_env_source_of_truth.md) 和 [hf_offline_mandatory](memory/remote/hf_offline_mandatory.md)。
- SGLang / diffusion 新模型远端跑之前必须做 diffusion detection preflight，并把结果写进 artifact：`from sglang.cli.utils import get_is_diffusion_model; print(get_is_diffusion_model(<model>))` 必须为 `True`；同时打印 `sglang`、`torch`、`HF_HOME`、`HF_HUB_CACHE`、`TRANSFORMERS_CACHE`、`XDG_CACHE_HOME`、`SGLANG_DIFFUSION_CACHE_ROOT`、`FLASHINFER_DISABLE_VERSION_CHECK`、`PYTHONPATH`、`CUDA_VISIBLE_DEVICES`。判定失败或 import 报错时先修 env/cache/overlay，不进入 generate/benchmark。
- 新 venv / cache 显式设置 `UV_CACHE_DIR`、`PIP_CACHE_DIR`、`XDG_CACHE_HOME`、`HF_HOME` 到宿主挂载根；缺依赖 / cache miss / 新建 venv 禁止写 `/root`、`/root/.cache`、容器层。
- 远端大目录清理优先同盘 `mv` 到 trash 后台删；30 秒内必须给阶段状态。物理删除不是目标，干净目录才是目标。
- Profiling 只有 `completed == num_prompts`、`failed == 0` 且日志显示真实请求完成，才可汇报 e2e / stage 数字。
- 共享 SSH 机器长跑用 tmux/nohup + 状态文件 + stop condition，避免密集 SSH 轮询。

### 2.4 Git / PR

- commit 默认 `git commit -s`，必须带 DCO sign-off。
- vLLM-Omni 代码仓库是 `D:\vllm-omni\vllm-omni`；主仓只作干净基准，业务改动必须在 `wt-<purpose>` worktree。
- 对 `D:\vllm-omni\vllm-omni` 写文件前，确认 git root 路径名匹配 `wt-*`。
- 开 PR 前、rebase / cherry-pick 后，跑 `git log --oneline origin/main..HEAD | nl` 和 `git diff --stat` 查污染。
- 写 PR 描述前读 `.github/PULL_REQUEST_TEMPLATE.md`；vLLM-Omni PR body 用 `Purpose / Test Plan / Test Result`。小 bugfix / reviewer-followup PR 只保留人读得懂的行为、复现和结果；不要机械填 `vLLM Version` / `vLLM-Omni Commit`，也不要把 GitHub checks、head SHA、旧 validation SHA 写成机器账本，除非用户明确要求 provenance 表或性能/精度证据需要绑定来源。
- 写 PR body 前先定 PR 类型和证据合同：小 bugfix 写最小行为回归和真实测试命令；性能/benchmark PR 写 metric contract、PR head、workload、命令和 artifact；拆分历史 PR 迁移原有有效证据并按新 scope 收窄；reviewer follow-up 先重读 live diff/comment，只答当前仍成立的问题。禁止把工作流水账、愿望式计划、相关但未跑的测试、local blocker、旧 head 证据写进公开 PR 描述。
- PR body 的 `Test Plan / Test Result` 只写能证明行为的语义测试、端到端验证、远端实测或 CI 结果。`ruff`、`compileall`、`git diff --check`、格式检查这类本地卫生检查不要写进公开 PR 描述；可以私下跑，但不能拿来充测试计划或测试结果。
- 性能 PR body 禁止发布探索 run / 半冷 run / 失败后修补口径作为 baseline。只有当前 PR head、最终配置、result JSON、server log 四者一致，且 `--assert-baseline` 或等价正式 sweep 通过后，才能写 e2e/qps/latency baseline；旧数值必须同步删除，不能用 caveat 留在正文里。
- 小 PR 的 `Test Plan` 优先写真实跑过的最小命令，通常是文件级 `pytest -q path/to/test_file.py` 或必要的单个目标；不要把相关测试函数名堆成清单来代替验证命令。`Test Result` 再用一句话说明该命令覆盖的核心回归行为。只有 reviewer 需要逐 case 映射时，才列具体 test function。
- 拆历史聚合 PR 时，新 PR 的 `Test Plan / Test Result` 必须优先迁移原 PR 已经跑过的仓上用例、远端命令、CI 结果和指标，并按新 PR scope 归类；禁止把已有结果改写成空泛的待跑计划。
- PR body / comment 的图片、指标、性能、精度证据必须做 provenance gate：PR head SHA、run checkout SHA、artifact mtime/size/hash 属于同一轮。
- 推 PR 前跑 `tools/pr_scope_gate.ps1`；触碰 `tests/`、`examples/`、`vllm_omni/entrypoints/`、`vllm_omni/model_executor/`、`vllm_omni/diffusion/` 时，scope ledger 必须逐文件说明 owner、必要性和测试绑定。
- 推送 `TaffyOfficial` PR 分支用 SSH identity：`git push git@github-taffy:TaffyOfficial/<repo>.git HEAD:<branch>`。

## 3. 下钻索引

- 总入口：[memory/MEMORY.md](memory/MEMORY.md)
- 错题本入口：[.claude_errors/_index.md](.claude_errors/_index.md)
- 远端服务器：[docs/remote_server.md](docs/remote_server.md)
- 远端记忆：[memory/remote/_index.md](memory/remote/_index.md)
- 远端调试：[memory/feedback/remote_debug_strategy.md](memory/feedback/remote_debug_strategy.md)
- 模型适配 PR：[memory/feedback/model_adaptation_pr_guardrails.md](memory/feedback/model_adaptation_pr_guardrails.md)
- 代码品味：[memory/feedback/code_taste.md](memory/feedback/code_taste.md)
- PR 工作流：[memory/feedback/pr_workflow.md](memory/feedback/pr_workflow.md)
- Reviewer lens：[memory/feedback/reviewer_lens_audit.md](memory/feedback/reviewer_lens_audit.md)
- CI 与测试错题：[.claude_errors/ci_and_testing.md](.claude_errors/ci_and_testing.md)
- 远端验证错题：[.claude_errors/remote_validation_workflow.md](.claude_errors/remote_validation_workflow.md)
- 远端 venv / 清理错题：[.claude_errors/remote_venv_and_cleanup.md](.claude_errors/remote_venv_and_cleanup.md)
- Profiling / 模型加载错题：[.claude_errors/profiling_and_model_loading.md](.claude_errors/profiling_and_model_loading.md)
