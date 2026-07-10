# vLLM-Omni 工作目录启动门禁

本文件只放必须先执行的硬门禁。通用方法下钻到 `framework/`，仓库、代码模块、模型和错题下钻到 `repos/`；目录维护规则见 `CONTRIBUTING.md`。

## 0. 开工顺序

1. 先判断任务场景，再读对应入口；不要把本文件当完整 runbook。
2. 写代码前读 [code taste](framework/review/guides/code-taste.md)。
3. 新模型 / 新 pipeline / 新 public entrypoint / 性能 claim PR，先读 [mini spec](framework/planning/guides/mini-spec.md)；涉及 vLLM-Omni 模型/checkpoint 再读 [model adaptation guardrails](repos/vllm-omni/review/guides/model-adaptation-guardrails.md)。
4. 远端 / GPU / serving / benchmark 前读 [通用远端入口](framework/remote/_index.md)、[vLLM-Omni 远端入口](repos/vllm-omni/remote/_index.md)；当前机器地址和路径只从 ignored `local/remote.md` 读取。
5. profiling / benchmark / 远端验证 / 新模型适配这类高风险任务，先查对应 `framework/` 方法、`repos/<repo>/` 指南和最近的 `incidents/`；旧经验只作候选，是否复用由当前版本、环境和证据决定。
6. 提交 / push / PR 前重读本文件 Git / PR 规则；commit 必须 DCO sign-off。
7. 写新经验或错题前先从 [通用入口](framework/_index.md) 和 [仓库入口](repos/_index.md) 查重复。新增或移动 Markdown 时必须同步最近的 `_index.md`，并跑 `python tools/check_knowledge_tree.py`；不进索引等于对路由不可见。落盘位置纪律见 P0「知识落盘纪律」。
8. 知识框架有写入就要有整理：本文件新增规则累计 ≥5 条、或距上次压缩超过一个月（看 [.claude/commands/memory-compact.md](.claude/commands/memory-compact.md) 底部 ledger），提醒用户跑 `/memory-compact` 做合并、拆分和索引体检。

## 1. P0 硬停（任何场景都适用）

- **Live facts > knowledge**：远端路径、模型 cache、venv、GPU、进程、env 以当前机器 live 证据为准，已有指南和错题只当线索。跑模型/benchmark 前在同一个 SSH/container/venv 或正在跑的 PID 上确认 `HF_HOME` / `HF_HUB_CACHE` / `TRANSFORMERS_CACHE` / `CUDA_VISIBLE_DEVICES` / cwd / command，用 `test -d` / `readlink -f` 验证 snapshot。
- **No fake evidence**：没有 grep / source / 实测证据不下结论。`shape clean`、`strict load`、stub smoke、PID 已死后的等待、`*_count=0`、fallback JSON 都不算有效证据。
- **知识落盘纪律**：所有长期知识只写本仓 `CLAUDE.md`、`framework/`、`repos/` 或设计说明 `docs/`；当前机器事实只写 ignored `local/`。禁止写任何系统 / 全局 / 个人 memory 位置（`C:\.codex`、用户目录 `.codex` / `.claude`、`$CODEX_HOME/memories`、ad-hoc note、reflect promotion 等）。用户要求“落盘 / 记住 / 复盘”时，稳定规则进入最近的 guide/rules/architecture，具体失败按根因进入最近的 `incidents/`，并同步 `_index.md`；不能形成可复用知识的流水账不落盘。
- **No silent fallback**：禁 `dict.get(...) or fallback`、`hasattr`、随手 `getattr(default)`、`generator=None` 类静默降级；临时 hack 必须显式 warning。
- **No broad kill/delete**：远端只清本轮 PGID / cwd / run dir 归属进程；删除前写 `KEEP` / `DELETE` 并确认交集为空。禁止宽泛 `pkill -f python`、禁止把用户要求保留的目录放进删除列表。
- **User correction refreshes evidence**：用户纠正或当前证据冲突时，停止维护旧结论，重读用户目标并重新查证；用户判断是高优先级线索，但最终结论仍绑定当前证据。
- **No optional commentary**：DO NOT send optional commentary。默认把时间花在 thinking、查证和验证上；除非用户要求状态、需要用户决策、遇到 blocker、长跑任务到达检查点或最终交付，否则不要发“我正在做 X / 接下来做 Y”这类进度口水。
- **汇报说人话**：先给结果和需要用户决定的事项，再补最少必要证据；内部术语只作证据，不套固定汇报模板。

## 1.5 场景触发器（命中即必读，读完才准开跑）

| 用户提到 | 必读 | 一句话硬约束 |
|---------|------|--------------|
| profiling / trace / 算子 / 时序图 / Perfetto / Nsight | [profiling 状态机](repos/vllm-omni/benchmark/guides/ar-graph-profiling.md)、[错题](repos/vllm-omni/benchmark/incidents/_index.md) | 默认交付 trace artifact（`trace_rank*.json(.gz)` / `.nsys-rep`）+ quality summary，benchmark stats 不准叫 trace profiling |
| 开图 / graph mode / `enforce_eager=false` 的 profiling | 同上（同轮 provenance gate 一节） | trace、请求、server 日志必须证明属于同一轮 graph run，缺任一项只能分别报告，不能说"开图 trace 已分析" |
| e2e / qps / latency vs 算子 / 气泡结论 | 同上 | benchmark 与 trace 是两类证据，禁止互相补位或合成结论 |
| UI / CLI 输出 / PR 公开说明 / 报告 / 可视化等用户可见行为 | [用户可见验收](framework/docs/guides/user-visible-acceptance.md) | 绿测不够，先定义普通用户路径验收并自己跑真实路径；用户手工抓到漏检必须同轮补 harness/check |
| 对标某产品 / 最低 parity / 产品书 / roadmap | [产品闭环规划](framework/planning/guides/product-loop-planning.md) | 先写用户可感知的完整产品闭环再拆 issue/PR/sub-agent，禁止按技术名词清单切片 |
| code review / PR 自审 / reviewer 打回 | [reviewer lens audit](framework/review/guides/reviewer-lens-audit.md) | 围绕当前 diff 查 duplication、owner、edge、public surface；涉及 async/IPC/resource/perf 时再增加对应审查，不用固定角色仪式 |
| loop / sub-agent / 并行 agent | [agent loop](framework/agents/guides/agent-loop-workflow.md) | 只在任务可独立并行且能降低盲区时使用；写入要隔离，结论和证据由主 agent 复核 |
| config / deploy / pipeline / cli cleanup 讨论 | [配置审计说人话](repos/vllm-omni/dev/guides/config-audit-plain-language.md) | 先讲"配置不是一个地方说了算"，围绕入口、默认值、多层加工、新老路径展开，代码名只作证据 |

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
- L4 perf baseline 更新开跑 / 改数前必须先做 config scope discovery：用 `test_name` / model / CI step 搜完整同组 config（例如同一模型的 TP/PP/SP/CfgP 变体）并列出 scope lock，禁止只改第一个失败 JSON。
- L4 perf baseline 证据只能来自对应 perf runner / result JSON 或用户明确给出的数值；functional L4 / step smoke / accuracy 只能作为功能验证，不能替代 perf baseline。已有 perf runner 必须先用仓库原命令跑；原命令跑不通时先修原命令或明确 blocker，禁止自造 wrapper / 临时 runner 掩盖问题。
- L2/L4 测试拆分必须先定义证据边界：L2 只做 CPU/mock 功能与 shape/dtype/metadata，不进入真实 stage/device 初始化；L4 才跑真实权重 accuracy/perf/profiling。mock 权重不等于 CPU-only，只有不触发 runner/stage/GPU 初始化才算 L2 功能 guard。
- 性能结果必须显式分类：`strict apples-to-apples`（同 model repo/snapshot + 同 pipeline 语义 + 同 request path + 同 defaults）、`workload-aligned only`（只同分辨率/帧数/steps/prompt）、`smoke only`（只证明能跑）。不是 strict apples-to-apples 时，禁止把差距解释成框架性能结论，只能说当前口径下的观测。
- 性能结论必须来自正式 sweep；endpoint 探索和单请求 smoke 只能证明路径可用。`ttfc_count=0` / `tpot_count=0` 写 unavailable。
- 已有 benchmark / smoke / offline inference 成功脚本时，先复用原脚本 + 最小改动。

### 2.3 远端 / 容器 / Slurm

- 远端路径 key 是完整 `user@host:port`，不同机器路径记忆不能混用。
- 先查任务工作根和用户点名路径；历史指南、错题和 `local/remote.md` 只当候选。用 `test -d` / `/bin/pwd -P` / import gate 验证 repo、worktree、venv 和版本后，再扩大搜索范围。
- 共享机器上他人 repo/venv 默认只读；未获明确授权禁止修改其代码、依赖、cache 或 Git 状态。需要写入的验证使用本轮 own clone/worktree 和 own venv/cache。
- 复杂命令写脚本文件，执行前固定 `wc -c`、`sed -n '1,40p'`、`bash -n`；避免 PowerShell/SSH 嵌套引号。
- PowerShell/Windows 投递到远端的脚本，执行前必须同时清 BOM 和 CRLF；wrapper 与它生成的 nested script 都要过 `perl -i -pe 's/^\x{FEFF}// if $.==1; s/\r$//' <script>`、`sed -n '1,40p'`、`bash -n`。出现 `﻿set: command not found`、路径带 `$'\r'`、`/bin/bash^M` 时先修脚本编码，不继续调业务逻辑。
- 远端安装 / 下载 / benchmark / 模型生成必须在远端脚本内加 `timeout` 或等价 watchdog，并分阶段写状态/日志；禁止只依赖本地 tool timeout。pip/uv/apt、模型下载、compile、serve、generate、pytest sweep 都要有明确超时、退出码和可轮询日志，卡在 uninstall/build/download 时必须能被远端超时切断。
- 启动服务 / benchmark 必须 fail-fast：先 `--help` 验证非平凡 CLI 参数；启动后同时监控 health、PID、日志错误签名；单请求 smoke 通过前不进 sweep。
- 远端 GPU / e2e / 大模型 pytest 开跑前必须先过模型缓存预检门，并把摘要发给用户或写进 artifact：`pwd`、`df -h`、`nvidia-smi`、`HF_HOME`、`HF_HUB_CACHE`、`HF_MODULES_CACHE`、`TRANSFORMERS_CACHE`、`XDG_CACHE_HOME`、`CUDA_VISIBLE_DEVICES`、`/data/models` 或 `/root/.cache/huggingface` 下目标模型是否已存在、cache 是否只读复用。默认优先 `HF_HOME=/data/models HF_HUB_CACHE=/data/models/hub HF_MODULES_CACHE=/data/models/modules`；如果复用 `/root/.cache/huggingface`，只能在已存在且 `snapshot_download(..., local_files_only=True)` 或本地绝对 snapshot 路径验证通过时只读使用。任何缺项、cache 不存在、`local_files_only` 失败、或需要写入/下载时直接停止，禁止先跑 pytest/serve/generate 让 HuggingFace 自动下载。
- HF 加载必须使用已验证的本地绝对 snapshot 路径，并设置 `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`；cache/env 细节见 [live environment](framework/remote/guides/live-environment.md) 和 [HF offline](framework/remote/guides/hf-offline-mandatory.md)。
- SGLang / diffusion 新模型远端跑之前必须做 diffusion detection preflight，并把结果写进 artifact：`from sglang.cli.utils import get_is_diffusion_model; print(get_is_diffusion_model(<model>))` 必须为 `True`；同时打印 `sglang`、`torch`、`HF_HOME`、`HF_HUB_CACHE`、`TRANSFORMERS_CACHE`、`XDG_CACHE_HOME`、`SGLANG_DIFFUSION_CACHE_ROOT`、`FLASHINFER_DISABLE_VERSION_CHECK`、`PYTHONPATH`、`CUDA_VISIBLE_DEVICES`。判定失败或 import 报错时先修 env/cache/overlay，不进入 generate/benchmark。
- 新 venv / cache 显式设置 `UV_CACHE_DIR`、`PIP_CACHE_DIR`、`XDG_CACHE_HOME`、`HF_HOME` 到宿主挂载根；缺依赖 / cache miss / 新建 venv 禁止写 `/root`、`/root/.cache`、容器层。
- 远端大目录清理优先同盘 `mv` 到 trash 后台删；30 秒内必须给阶段状态。物理删除不是目标，干净目录才是目标。
- Profiling 只有 `completed == num_prompts`、`failed == 0` 且日志显示真实请求完成，才可汇报 e2e / stage 数字。
- 共享 SSH 机器长跑用 tmux/nohup + 状态文件 + stop condition，避免密集 SSH 轮询。

### 2.4 Git / PR

- commit 默认 `git commit -s`，必须带 DCO sign-off。
- vLLM-Omni 代码仓库是 `D:\vllm-omni\vllm-omni`；主仓只作干净基准，业务改动必须在 `wt-<purpose>` worktree。对主仓的 Write/Edit 已由 `.claude/hooks/wt-write-guard.sh` 硬拦截；bash 内重定向 / `sed -i` 等写入不经过 hook，仍须自查 git root 匹配 `wt-*`。
- 开 PR 前、rebase / cherry-pick 后，跑 `git log --oneline origin/main..HEAD | nl` 和 `git diff --stat` 查污染。
- 写 PR 描述前读 `.github/PULL_REQUEST_TEMPLATE.md`；vLLM-Omni PR body 用 `Purpose / Test Plan / Test Result`。小 bugfix / reviewer-followup PR 只保留人读得懂的行为、复现和结果；不要机械填 `vLLM Version` / `vLLM-Omni Commit`，也不要把 GitHub checks、head SHA、旧 validation SHA 写成机器账本，除非用户明确要求 provenance 表或性能/精度证据需要绑定来源。
- 写 PR body 前先定 PR 类型和证据合同：小 bugfix 写最小行为回归和真实测试命令；性能/benchmark PR 写 metric contract、PR head、workload、命令和 artifact；拆分历史 PR 迁移原有有效证据并按新 scope 收窄；reviewer follow-up 先重读 live diff/comment，只答当前仍成立的问题。禁止把工作流水账、愿望式计划、相关但未跑的测试、local blocker、旧 head 证据写进公开 PR 描述。
- 多 PR / stacked PR / release-candidate 合入前必须先选唯一 merge vehicle：要么逐个窄 PR 合，要么 integration PR 合。选 integration PR 后，窄 PR 只能作为历史切片 / review reference，ready 前必须清掉 PR body/docs/bot comment 里的 draft/WIP/stale wording，合入后立即 comment + close superseded PR。新增修复必须绑定用户路径、验收缺口或明确 P1/P2 finding；状态机洁癖和 nice-to-have 不进当前 PR。细则见 [integration PR](repos/vllm-omni/git/guides/integration-pr-merge-vehicle.md)。
- PR body 的 `Test Plan / Test Result` 只写能证明行为的语义测试、端到端验证、远端实测或 CI 结果。`ruff`、`compileall`、`git diff --check`、格式检查这类本地卫生检查不要写进公开 PR 描述；可以私下跑，但不能拿来充测试计划或测试结果。
- 性能 PR body 禁止发布探索 run / 半冷 run / 失败后修补口径作为 baseline。只有当前 PR head、最终配置、result JSON、server log 四者一致，且 `--assert-baseline` 或等价正式 sweep 通过后，才能写 e2e/qps/latency baseline；旧数值必须同步删除，不能用 caveat 留在正文里。
- 小 PR 的 `Test Plan` 优先写真实跑过的最小命令，通常是文件级 `pytest -q path/to/test_file.py` 或必要的单个目标；不要把相关测试函数名堆成清单来代替验证命令。`Test Result` 再用一句话说明该命令覆盖的核心回归行为。只有 reviewer 需要逐 case 映射时，才列具体 test function。
- 拆历史聚合 PR 时，新 PR 的 `Test Plan / Test Result` 必须优先迁移原 PR 已经跑过的仓上用例、远端命令、CI 结果和指标，并按新 PR scope 归类；禁止把已有结果改写成空泛的待跑计划。
- PR body / comment 的图片、指标、性能、精度证据必须做 provenance gate：PR head SHA、run checkout SHA、artifact mtime/size/hash 属于同一轮。
- 推 PR 前跑 `tools/pr_scope_gate.ps1`；触碰 `tests/`、`examples/`、`vllm_omni/entrypoints/`、`vllm_omni/model_executor/`、`vllm_omni/diffusion/` 时，scope ledger 必须逐文件说明 owner、必要性和测试绑定。
- 推送 `TaffyOfficial` PR 分支用 SSH identity：`git push git@github-taffy:TaffyOfficial/<repo>.git HEAD:<branch>`。

## 3. 下钻索引

- 通用经验：[framework/_index.md](framework/_index.md)
- 仓库经验：[repos/_index.md](repos/_index.md)
- vLLM-Omni：[repos/vllm-omni/_index.md](repos/vllm-omni/_index.md)
- Jianghan：[repos/jianghan-roleplay-data-pipeline/_index.md](repos/jianghan-roleplay-data-pipeline/_index.md)
- 远端通用指南与错题：[framework/remote/_index.md](framework/remote/_index.md)
- vLLM-Omni 性能指南与错题：[repos/vllm-omni/benchmark/_index.md](repos/vllm-omni/benchmark/_index.md)
- HunyuanImage3：[repos/vllm-omni/models/hunyuan-image3/_index.md](repos/vllm-omni/models/hunyuan-image3/_index.md)
- 当前机器信息：ignored `local/remote.md`
- 贡献与目录维护：[CONTRIBUTING.md](CONTRIBUTING.md)
