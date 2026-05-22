# Claude Code Workflow Starter — 硬卡点规则手册

本文件是**硬卡点规则手册**：宪法 + 一句话规则 + 链接。rationale / incident 详情全在 `memory/` 和 `.claude_errors/`，命中场景再点链接。

**怎么用**：会话开头扫宪法 P1-P8 建框架；写代码前必须读 [code_taste](memory/feedback/code_taste.md)；场景命中下沉到对应硬规则；踩新坑追加到 `.claude_errors/<topic>.md`（格式见 [claudeception skill](skills/claudeception/SKILL.md)），同坑 ≥2 次升级为硬规则时**必须标 P1-P8 派生**。写新 memory / error 前先查 [memory/MEMORY.md](memory/MEMORY.md)，能套现有主题就追加章节，**禁建小文件**（新建需三条件齐：现有主题无法容纳 + 预期复用 ≥2 次 + 通用主题而非具体 incident）。

> 这个仓库是**通用模板**。把你项目的实战经验通过飞轮（`.claude/hooks/stop-gate.sh` 自动触发）沉淀到 `.claude_errors/`，同坑 ≥2 次再升级为硬规则；E 节是"项目国策"占位，按你的架构填具体约束。

---

## 🏛️ 宪法（8 条原则）

> A-F 硬规则是这 8 条在具体场景的派生。规则未覆盖的新场景先回这层推。

- **P1 证据先行**：未实测验证不算证据，禁据此下结论；algorithm 决策必先 grep upstream → B2 / B7 / B8 / B9 / B14 / B18 / B19 / **B30** / **B32** / F1
- **P2 简单直接，意图先行**：同等需求选最简方案；用户给明确方案直接执行；极简指令先还原意图 → B3 / B4 / B5 / B6 / F2 / F6
- **P3 完整链路而非单点**：bug 先完整 pipeline 静态 trace；style/bias 先 diff 代码非 dump 数值；framework hack 和 algorithm fix 都能解释时选 algorithm → B12 / B13 / B20 / **B31**
- **P4 单变量隔离归因**：多处改动同时跑通后必做最小消除实验逐处 revert；"看到 diff" ≠ "diff 就是 root cause"；同时持有 ≥2 个怀疑禁止动手 fix，先静态二分 → B14 / B15 / B16 / **B32**
- **P5 测试要打到真实路径**：e2e 默认优于 mock；对齐测试 reference 必从被测对象 snapshot 加载不能用自己副本；input 对齐 ≠ output 对齐 → B17 / C2 / C3 / C5 / **C8**
- **P6 拒绝静默降级**：禁 `dict.get or` / `hasattr` / `generator=None` 类 silent fallback；schema 报错先问"约束对吗"再改；hack 必 `logger.warning` 留痕 → F7
- **P7 范围自律**：小 PR `git show` 整段读 + 审悬挂引用；测 PR 先看首 commit message；compound dep 错逐个 fix forward；调试期"顺手优化"延后独立 PR → A6 / A7 / D3 / F3 / **F8**
- **P8 代码品味**：写代码前先读 code_taste；人工 reviewer 先看命名/归属/复用/测试位置/注释/API 面/diff 气味，能跑不等于可 review → **C8** / **F10** / [code_taste](memory/feedback/code_taste.md) / [reviewer_lens_audit](memory/feedback/reviewer_lens_audit.md)

---

## ⚠️ 硬性规则（按场景分组）

### A. 远端 / 容器 / Slurm
- **A1** 远端发命令后先短 sleep（≤5s）+ capture 确认脚本真启动（`collected N items` / 程序日志），再长 sleep 等结果 → [remote_debug_strategy](memory/feedback/remote_debug_strategy.md)
- **A2** 退 srun 前必须容器内 `pkill -9 -f <你的进程名>`，否则占死 GPU → [srun_lifecycle](memory/remote/srun_lifecycle.md)
- **A3** 容器内一切持久内容（模型/venv/缓存/代码）必须写宿主挂载路径，别写 `~/.cache` / `/tmp` / 容器层 → [container_setup](memory/remote/container_setup.md)
- **A4** 进新节点先 `docker inspect <other_container>` 看挂载，别信文档别假设路径 → [node_basics](memory/remote/node_basics.md)
- **A5** 切换包源前先确认网络环境；默认直连官方源，错配镜像会拉到旧/损坏的 wheel → [node_basics](memory/remote/node_basics.md)
- **A6** tmux window 有前台进程时不能往该 window 发 shell 命令（send-keys 进了进程 stdin），从另一个 window 发
- **A7** 跨节点/PowerShell→SSH 执行复杂命令用脚本文件，禁止嵌套引号；远端脚本落盘后必须 `wc -c` + `sed -n '1,40p'` + `bash -n` 查空文件/BOM/本地变量展开（`ssh nodeA "docker exec $(...) ..."` 的 `$()` 在本地展开必错）→ [remote_debug_strategy](memory/feedback/remote_debug_strategy.md)
- **A8** 进容器后必须 `unset TRANSFORMERS_CACHE` 和 `HF_HUB_CACHE`，两个都覆盖 `HF_HOME`；空字符串 ≠ unset → [container_setup](memory/remote/container_setup.md)
- **A9** 容器内跑 multiprocessing 前 `cd /tmp`，避免 spawn 子进程 chdir 到 Lustre 报 `PermissionError` → [container_setup](memory/remote/container_setup.md)
- **A10** 释放资源三步：容器内 pkill → exit docker exec → exit srun → `squeue -u <user>` 确认空 → [srun_lifecycle](memory/remote/srun_lifecycle.md)
- **A11** 远端跑任何 HF 加载（`from_pretrained()` / 框架 init 调用）前必先 `export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`；只设 `HF_HOME` **不够**（hub 仍校验 revision / 补 shard），大模型一启动就把网络+磁盘打爆可导致 SSH 断连。或传本地绝对 snapshot 路径替代 repo id → [hf_offline_mandatory](memory/remote/hf_offline_mandatory.md)
- **A12** 远端验证 / GPU smoke / 远端 pytest 前必须先读 `docs/remote_server.md`；以 `$WORK_DIR` 为稳定锚点，每次默认新建本次专用 worktree + `.venv`（旧 `wt-*`/venv 会被清理，禁写死复用），但新终端接手已有远端任务时先整理 head/worktree/venv/tmux/out_dir 5 行 runbook 并复用已知目录，不要全盘 rediscover；本地 commit+push 后远端 git fetch/checkout 同步，venv 健康检查通过再测；旧 PR/历史分支先做 base commit import/init smoke，base 起不来只算环境/ABI blocker；禁 `scp` / `git diff | ssh apply`。但纯 lint / 小范围静态修复已在本地通过时，不要默认上远端；远端只用于本地缺依赖、GPU/e2e、环境相关或用户明确要求 → [.claude_errors/remote_and_ssh.md](.claude_errors/remote_and_ssh.md)

### B. 调试方法论
- **B1** 调试阶段禁 git commit-push-pull 循环；远端直接写 `/tmp/test_xxx.py` 试错；commit message 出现 "fix attempt N" 立刻停 → [remote_debug_strategy](memory/feedback/remote_debug_strategy.md)
- **B2** 接新模型/新依赖前先做环境侦察（config JSON / 目录列表 / HF cache / 包版本 / 同类先例），结果留痕 → [remote_debug_strategy](memory/feedback/remote_debug_strategy.md)
- **B3** 奥卡姆剃刀：最少资源最简配置先试（小卡数小 TP，OOM 再加）；硬编码资源要求必须有实测依据
- **B4** 用户给明确技术方案时直接执行，禁止"先试试不改看行不行" → [execution_principles](memory/feedback/execution_principles.md)
- **B5** 优先最简单直接的方案，禁绕远路（venv 优于 PYTHONPATH hack / pip 升级系统包） → [execution_principles](memory/feedback/execution_principles.md)
- **B6** 已知结论（error book / memory / 上轮调试）直接应用，禁重新推导 → [execution_principles](memory/feedback/execution_principles.md)
- **B7** 测模型 baseline 前必先 grep 官方 README/demo 找 entrypoint API，禁自己拍参数替代官方 `generate()` / `pipeline()` → [feedback_hf_trust_remote_code](memory/feedback/feedback_hf_trust_remote_code.md)
- **B8** 怀疑某 op 是 bug 前必先 grep 日志确认它真被调用（硬编码 backend / feature flag 可能让你 debug 的 kernel 根本没跑）
- **B9** 标某统计指标"异常"前必须用官方/参考实现做 baseline 对照；单边 dump 不算证据（模型设计可能反直觉：attention sink / outlier channel / post-LN 信息洗除）
- **B10** swap"等价"实现前先列接口 diff 矩阵（`__init__` / forward 签名 / config 字段 / kwarg 名 / return type），写 adapter shim 一处 reconcile 再 sed
- **B11** 远端 patch session 开头和切大假设前必须 `grep -rn "BUG-PROBE"` 全量审计；探针 vs 实验 patch 用不同 marker；实验性数值改动 env-var gate 不改默认
- **B12** [P3 派生] 风格/质量 bias bug 第一步是静态代码 diff 不是数值 dump（指纹在 dispatch 决策 / RoPE phase / activation 翻号，不在 mean/std）
- **B13** [P3 派生] repo 同时有两套实现（如 AR 版 + DiT 版 / eager 版 + compiled 版）→ **先 diff 两边**（一边修过的 bug 高概率另一边漏同步）
- **B14** [P1 派生] prior session "X 已证伪"只对具体 hypothesis 成立，不代表组件清白；"几个团队同 bug" ≠ infra 回归（可能都漏了同款 fix）
- **B15** [P4 派生] 多处同时改后跑通**不能独立归因**——N 处只有 1 处真起作用，其它是 cargo cult；声明 root cause 前必做最小消除实验逐处 revert/toggle
- **B16** [P4 派生] 静态 diff 找到差异 → 假设 → 隔离实验 → 才确认机制；"看到 diff" ≠ "diff 就是 root cause"；尤其 class 替换先看继承结构 / wrapper hooks 再看实现细节
- **B17** [P5 派生] 跨实现数值对比（PSNR / cosine sim / KL）前必须 fair-comparison checklist 显式对齐（prompt / 输入字节 / seed / **temperature=0** / **top_k=1** / guidance / steps / 分辨率）；sampling mode 自带 floor（如 PSNR 5-15 dB），未切 greedy 不许声称"实现 B 有问题"
- **B18** [P1 派生] 用户问"为什么不 X" / 给工程方案前必先 grep / 看 yaml / 看架构核对 X 机制是否真实存在；"工作量 N 天"凭空想象必被怼
- **B19** [P5 派生] cross-impl 对齐验证前必先测 reference 自身 reproducibility（同 seed 同 greedy 跑两次比指标）；同实现自比都达不到的水平不要去要求 cross-impl 达到
- **B20** [P3 派生] 输出尺寸 / 形状异常按 prompt → 中间层 → 最终输出逐层 trace，别先扣单个显眼函数
- **B21** [P3 派生] 用户报"路径 A 一直 X，路径 B 一直 Y" = systematic 跨路径偏差，**禁用 CUDA/MoE non-determinism 解释**（那是 stochastic）；对齐三件套：tokenized input 字节同 / multi_modal_data 字节同（**PIL RGBA→RGB silent bug**：黑底 vs 白底）/ sampling_params 一致 → [systematic_vs_stochastic_divergence](memory/feedback/systematic_vs_stochastic_divergence.md)
- **B22** [P1 派生] spawn review sub-agent 时 prompt **禁塞自己 hypothesis / focus**（"重点查 X" = 偏见通过 prompt 传染过去）；要么开放式 audit（"列所有问题分级 P0/P1/P2"），要么并行多 framing union → [review_delegation_framing](memory/feedback/review_delegation_framing.md)
- **B33** [P1+B22 派生] sub-agent review prompt **禁用** "code check 一下" / "看有没有问题" / "review 一下" 类开放但无 audit 框架的 framing——子 agent 必答 "OK" / "no issues found"，护不住，reviewer 一上来就打回。必须用 reviewer-lens 4 项 audit 模板（duplication / layering / edge cases / surface area）显式列每项要返回的 finding 或 "none found"，或起 3 个 sub-agent 各跑一项 union → [reviewer_lens_audit](memory/feedback/reviewer_lens_audit.md)
- **B23** [P4 派生] TaskCreate 列**枚举步骤**（"该检查的事"）不是修复目标（"已知要修的事"）；sub-agent 返回 action list 当 ground truth 前必开 meta-task 独立 re-enumerate → [task_as_audit_enumeration](memory/feedback/task_as_audit_enumeration.md)
- **B24** [P1 派生] reviewer / 同事说"正常 X" / "应该 X" / "通常 X" = invariant 是 **bug detector 不是 design intent**；触发 → grep / 实测；观察 ≠ X 立刻进根因模式，**禁**找台阶（"design choice" / "次优但 acceptable"） → [conclusion_discipline](memory/feedback/conclusion_discipline.md)
- **B25** [P3 派生] 声明"X harmless / 次优但正确 / 不需要修"前必须写完整因果链 "X → path P → Y → 被 Z 截断/丢弃 → 不到 final output" + 列**所有副作用**（latency / compute / 状态污染 / 下游污染）；链不完整不准用 harmless → [conclusion_discipline](memory/feedback/conclusion_discipline.md)
- **B26** [P1 派生] 嘴上 / commit message / 结论必须带前缀 **"推理：（从 source 看）"** 或 **"实测：（跑过 X，证据 Y）"**；混说 = 用推理冒充实测 = 撒谎 → [conclusion_discipline](memory/feedback/conclusion_discipline.md)
- **B27** [P3 派生] crash / AttributeError / 任意 exception = **trace upstream 起点不是 stop sign**：必须 trace "为啥这个 path 拿到 wrong-type"；**禁** revert 上一步 + 宣告"这条路不通"（第一次 crash 已给根因位置）
- **B28** [P1+P2 派生] 用户 **≥ 2 次** 说"X 有问题" / 反驳同一结论 → **立即翻盘**到用户判断当 ground truth；禁继续找新角度的台阶（"换个层面看" / "再补充一下"）；两次反驳 = 我立场就是错 → [conclusion_discipline](memory/feedback/conclusion_discipline.md)
- **B29** [P2 派生] 用户给具体 fix 指令 + 修改点 identified → **直接动手** edit / commit / push / 测试；**禁** detour 去 read sibling 实现 / "确认一下 X 怎么做"（confirmation seeking 伪装成 due diligence） → [conclusion_discipline](memory/feedback/conclusion_discipline.md)
- **B30** [P1 派生 + B7 扩展] algorithm 决策（stop 条件 / EOS / sampling 策略 / 特殊 token / generate loop / KV 切片或 snapshot 触发点 / prompt 模板 / system prompt 注入位置）前必先 grep upstream 主入口（`modeling_*.py` / `generation_*.py` / `tokenization_*.py`）；upstream repo 已 clone 不读 = 自废武功 → [upstream_first_for_algorithm](memory/feedback/upstream_first_for_algorithm.md)
- **B31** [P3 派生] 同现象 framework hack（加 config / middleware / defer）和 algorithm fix（改 stop / sampling / prompt）都能解释时 **default to algorithm fix**；信号：hack 注释含"为了应付 X 特殊情况" / 多 hack 互依赖必须一起 work / 加 hack 后还要 extra check 防 hack 崩 → [algorithm_vs_framework_fix](memory/feedback/algorithm_vs_framework_fix.md)
- **B32** [P1+P4 派生] 调试漏斗：grep 优先于实测、收敛到 1 个怀疑再动手、user 给诊断 ≠ user 给修法。连续 ≥2 次实测仍未定位**强制回静态**；同时持有 ≥2 个独立怀疑**禁止动手 fix**（先静态二分到 1 个）；user 给现象/诊断时写代码前必先 AskUserQuestion framing 修法 scope，**禁脑补"按 X 真值表改函数 + 加参数 + 改 call site"扩散式修法**（B29 反向场景，B29 管 user 给 fix 指令）→ [debug_funnel_discipline](memory/feedback/debug_funnel_discipline.md)

### C. CI / 测试
- **C1** 做"团队同款 CI"先打开 `tests/` 现有文件看一眼，别基于幻觉讨论方案 → [always_inspect_existing_tests_first](memory/ci/always_inspect_existing_tests_first.md)
- **C2** 写 accuracy test 时所有 CLI 参数必须从 fixture 透传到 benchmark（`--samples-per-type` / `--max-samples` 漏传 = 跑全量数据集，smoke 变几小时）
- **C3** 离线环境（`HF_HUB_OFFLINE=1`）跑 accuracy test 前 checklist：generate model / judge model / dataset 三项齐全 `ls $HF_HOME/hub/ | grep models--`
- **C4** 跑远端脚本前过启动前三连：(1) GPU 空闲 (2) 模型路径存在 (3) 缓存变量正确；kill 进程后必 `sleep 5 + nvidia-smi` 确认显存归零
- **C5** [P5 派生]"本地实现对齐参考实现"回归测试四红线：(a) 参考实现必须从原仓库/snapshot 加载，不能 `from <自己包>` 导入自副本 (b)"X 输出"默认 generated output 解读，input prefill 简化必须显式 ack (c) 跑通的 yaml / 路径不许无解释替换 (d) 两侧 input 必须从同一句 regression intent 派生，**禁从 benchmark/example 脚本抄输入**
- **C6** 加/改 CI 测试、dummy guard、smoke test、PR-level watch test 时 `compileall` + `git diff --check` **不算验证**；新增/改的测试函数必须实跑一次；本地缺 deps 用 venv / 容器 / 最小脚本走相同 core path；跑不动就显式声明阻塞，禁声称"已验证"。dummy 用 `object.__new__` 时不能假设 attr 可写，read-only property 在 class 级 monkeypatch
- **C7** 提交/推 PR 前必须跑覆盖本次改动文件的 `ruff check`（需要时再跑 `ruff format --check` 或 pre-commit 对应 hook）；只跑 `py_compile`/pytest 不够。CI 报 ruff 失败视为本地验证漏项，修完必须 amend+push 并复跑 → [.claude_errors/ci_and_testing.md](.claude_errors/ci_and_testing.md)
- **C8** [P5+P8 派生] 新增/修改 `stream` 参数、SSE chunk、WebSocket message、OpenAI-compatible streaming schema 时，必须先 diff 仓库已有 streaming endpoint 的异常语义，并补坏路径测试：structured 4xx 不能丢成 500、`EngineDeadError` 不能被 generic error chunk 吞掉、`delta` 必须能客户端 append 重建最终状态、`[DONE]` 分支明确。只测 200 + happy chunks 不够 → [.claude_errors/ci_and_testing.md](.claude_errors/ci_and_testing.md) / [reviewer_lens_audit](memory/feedback/reviewer_lens_audit.md)

### D. Git / PR
- **D1** git commit 默认加 DCO sign-off（`-s`），缺 sign-off 上游 CI 拒绝
- **D2** 开发在 git worktree 里做，主仓库工作区保持干净；命名 `wt-<purpose>`，完事 `git worktree remove`
- **D3** 开 PR 前 + cherry-pick/rebase 后必跑 `git log --oneline origin/main..HEAD | nl` 逐条查污染；`git diff --stat` 改的文件应跟 PR 主题强相关，无关文件 >1-2 个就要查 → [git_and_pr_branch_pollution](.claude_errors/git_and_pr_branch_pollution.md)
- **D4** 主仓分支保持 `main` 干净只作基准同步源：开工前 `git fetch origin main` + `git pull --ff-only origin main`，必要时 `git reset --hard origin/main` 强制对齐；禁止在主仓工作区写业务改动，代码工作一律另开 worktree
- **D5** 写 PR 描述前必须读仓库 `.github/PULL_REQUEST_TEMPLATE.md`；按项目约定格式（Purpose / Test Plan / Test Result）写，不要用通用模板覆盖项目模板。新增 public API 字段 / CLI 参数 / SSE schema / OpenAI-compatible 参数时，PR 前必须同步对应 docs → [git_and_pr_branch_pollution](.claude_errors/git_and_pr_branch_pollution.md)
- **D6** 业务代码/测试代码写完并准备提交或推 PR 前，必须开 sub-agent 做 reviewer-lens audit（duplication / layering / edge cases / surface area）并结合 code_taste 审 diff；不能等用户手动提醒。sub-agent finding 必须先处理或明确记录不处理理由，再 commit/push → [reviewer_lens_audit](memory/feedback/reviewer_lens_audit.md)

### E. 架构国策（项目占位）
> 在这里填**你项目的硬性架构约束**，会比通用规则更高优先级。示例（按你项目改写或删除）：
> - 改 `<config registry>` 而不是 YAML；改 YAML 是用户 CLI；不引入新 JSON/YAML 启动配置文件
> - 新增 op/kernel 必须先 grep 看 `<框架核心目录>` 有没有现成实现
> - 跨进程通信只走 `<约定的 IPC 通道>`，不允许塞共享内存指针

### F. 编码行为
- **F1** 动手前先说明假设；多种解读时列全部方案不要悄悄选一个；不确定就停下问
- **F2** 只写够用的最少代码：不加未被要求的功能/抽象/灵活性；200 行能 50 行写就重写（B5 管选型，F2 管体积）
- **F3** 只碰任务直接涉及的代码：不顺手优化周边、不改风格、不删无关死代码；匹配既有命名/缩进；只清理自己改动产生的孤儿
- **F4** 多步任务先列 `1. [步骤] → verify: [如何确认]` 计划再执行；"应该能跑"不算验证
- **F5** 第一性原理：设计决策先问"根本约束是什么"，从约束往上推方案，不靠类比或惯例拍脑袋
- **F6** 奥卡姆剃刀：同等需求选最简方案；不引入多余层次/概念/依赖（B3 管资源量，F6 管方案复杂度）
- **F7** [P6 派生] 拒绝静默降级：禁 `dict.get("k") or fallback` / `hasattr` / `getattr(obj, "k", default)` / `generator=None`；schema 报错先问"约束本身对吗"再决定改 input 还是改 schema；任何 hack 必 `logger.warning` 留痕
- **F8** [P7 派生 + F3 加强] 调试/PR 主线发现"顺手优化"必**分类**：(a) 主线必需（删掉主线 broken / test fail / crash）→ 留下；(b) 周边收益（latency / 可读性 / 别处少绕一圈）→ **延后独立 PR**；信号 = commit message 想分两段 / reviewer 能独立 review 不依赖主线；**禁** commit 出现 "plus housekeeping" / "顺手 fix" / sunk-cost "都写完了不删可惜" → [narrow_optimization_scope](memory/feedback/narrow_optimization_scope.md)
- **F9** Windows/PowerShell 打开文本一律 UTF-8：优先显式 `Get-Content -Encoding utf8` / `Set-Content -Encoding utf8`；本机已在 PowerShell profile 设 `Get/Set/Add-Content` 和 `Out-File` 默认 UTF-8，但仍不要依赖 Python 环境变量解决 PowerShell 文件解码
- **F10** [P8 派生] 写任何代码前必须读 [code_taste](memory/feedback/code_taste.md)。代码品味不是 push 前 pass：动手前就要按人工 reviewer 视角检查命名是否说清机制、逻辑是否住在数据 owner、helper 是否复用、测试是否放行为 owner、注释是否解释策略、API knob 是否必要、diff 是否有临时补丁味；新增参数必须同步 docstring contract，generic helper 命名不能泄漏 caller-specific 语义；optional tensor/cache/staged 参数必须拆 data contract + execution-context contract，wrong caller 要在 owner 边界早炸。

---

## 索引

- 项目记忆主入口：[memory/MEMORY.md](memory/MEMORY.md)
- 远端服务器：[docs/remote_server.md](docs/remote_server.md)（不存在时从 `docs/remote_server.template.md` 复制；问用户填 SSH 用户名/IP/密码、节点 hostname、Slurm 分区、工作目录、容器名、tmux session；已在 `.gitignore`）

## 包管理

- 远端容器内一律 `uv pip install`，不用原生 `pip install`
- uv 在 Lustre 挂载目录报 `uv.toml` permission denied，先 `cd /tmp` 再执行
