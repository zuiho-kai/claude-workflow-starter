# Memory · feedback/

**何时来翻**：每次会话开头扫一眼，避免重犯过的错。`execution_principles.md` + `remote_debug_strategy.md` 是高频，**先读这俩**。

| 文件 | 一句话 |
|------|--------|
| [execution_principles.md](execution_principles.md) | 执行类合集：简单方案优先 / 用户给方案直接执行 / 已知结论直接用 / 简短指令先还原意图 / 仓库上下文落盘写本仓长期记录 / IP+port 先 probe / 连环 dep 错别 bail / Windows 文本显式 UTF-8 |
| [remote_debug_strategy.md](remote_debug_strategy.md) | 远端调试入口：基础侦察 / serving fail-fast cleanup / AR graph profiling / full pipeline benchmark 分页下钻 |
| [pr_workflow.md](pr_workflow.md) | PR 工作流入口：branch-push-rebase / review-debug-test / PR body evidence / scope narrowing 分页下钻 |
| [alignment_debug.md](alignment_debug.md) | vllm-omni ↔ HF 对齐调试合集：先 grep 显式随机源 / multimodal placeholder 改前读完整 routing / input 对齐 ≠ 输出对齐 / 拆账目别笼统归 BF16 |
| [size_debug.md](size_debug.md) | 背景生图 / 多图尺寸与比例异常：按 prompt -> AR -> bridge -> DiT -> config/token 逐层 trace |
| [style_bias_debug_methodology.md](style_bias_debug_methodology.md) | 风格/质量 bias 类 bug 第一步是静态 diff 不是 dump；MoE gate dtype / Norm / RoPE 是高 yield 区域 |
| [plan_and_validation.md](plan_and_validation.md) | Plan / validation 入口：核心验证原则 / PR 规格锚定 / L2/L4 split / benchmark scope / 远端 benchmark/accuracy 证据 gate / 远端长测 gate / AR graph profiling 机制；具体 Hunyuan 复跑参数下沉 archive |
| [vllm_omni_omni_init_args.md](vllm_omni_omni_init_args.md) | bypass argparse 直接 `Omni(...)` 必须 nullify EngineArgs 顶层 tp/pp/prefix_caching 默认值；不然跟 stage_config yaml 冲突 |
| [codex_review_lessons.md](codex_review_lessons.md) | Codex review 学到的 2 个 API 设计习惯：从 producer 引 enum 不要 hardcode 字面值；暴露 enum 时也暴露 custom override escape hatch |
| [seed_determinism_audit.md](seed_determinism_audit.md) | "同 seed 出不同图" 的 audit checklist：先确认 sampling 是 greedy 还是 stochastic；greedy 下漂移=CUDA/MoE non-det，不是 seed 代码 bug；别 P0 处理浪费时间 |
| [systematic_vs_stochastic_divergence.md](systematic_vs_stochastic_divergence.md) | "路径 A 一直 X，路径 B 一直 Y" 是 systematic 不是 stochastic——禁止用 CUDA/MoE non-det 解释；AR 输入对齐要 prompt + image tensor + sampling 全部 3 pillar；PIL mode RGBA vs RGB 是 silent bug 源（PR #3444 实测踩坑）|
| [review_delegation_framing.md](review_delegation_framing.md) | Spawn review sub-agent 时不能传自己的 hypothesis/focus；子 agent 严格在 prompt 框定的范围内审查，框外问题全漏。要么开放式 audit 要么并行多 framing union |
| [reviewer_lens_audit.md](reviewer_lens_audit.md) | 自审 + sub-agent review 必跑的 4 条 audit：duplication / layering / edge cases / surface area。Sub-agent 说"OK"是弱信号；rebase 后要把 conflict/auto-merged 文件和 current reviewer threads 当 fresh diff 重审；merge 前还要跑 committer/project-owner framing |
| [code_taste.md](code_taste.md) | **写代码前必读**：人工 reviewer 代码品味规则。命名必须说清机制，逻辑住在数据 owner，新增 helper 先 grep 复用，测试放行为 owner，注释解释策略，API knob 默认不加；新增执行路径必须复用 request parsing owner helper；shared serving/chat path 改 multimodal key 前必须 grep 跨模型 consumer |
| [model_adaptation_pr_guardrails.md](model_adaptation_pr_guardrails.md) | 新模型 / 新 pipeline 适配 PR gate：开发前 mini spec、checkpoint layout、public entrypoint matrix、request parsing parity、all-or-none prompt fields、PR body provenance、interactive reviewer loop |
| [task_as_audit_enumeration.md](task_as_audit_enumeration.md) | TaskCreate 列**枚举步骤**不是修复目标；把外部 review action list 直接当 task = 继承外部盲点。API rename 后必须开 cross-product grep task，加 producer 新字段必须开 producer→consumer trace task |
| [conclusion_discipline.md](conclusion_discipline.md) | 下结论的纪律流程化清单：invariant=bug detector / harmless 必须有完整因果链 / 推理 vs 实测前缀 / crash=trace 起点 / 用户 ≥2 次反驳必翻盘 / 有 fix 指令禁 detour / **自评成果禁"看起来 OK"——必须 reference 比对 + 重读自己警告 + 主动列失败模式**（B24-B29 + 规则 8 来源）|
| [upstream_first_for_algorithm.md](upstream_first_for_algorithm.md) | Algorithm-level 决策（stop token / sampling / 特殊 token / KV cache 切片 / generate loop）前先 grep upstream 源码——B7 精神扩展（B30 来源）|
| [algorithm_vs_framework_fix.md](algorithm_vs_framework_fix.md) | 同一现象 framework 层 hack 和 algorithm 层 fix 都能解释时 default to algorithm fix；多个 framework hack 互依赖 = cargo cult 信号（B31 来源）|
| [narrow_optimization_scope.md](narrow_optimization_scope.md) | 调试中"顺手优化"必须分类：主线必需带，附赠收益延后独立 PR；F3 派生加强（F8 来源）|
| [debug_funnel_discipline.md](debug_funnel_discipline.md) | 调试漏斗：grep 优先于实测 / 怀疑收敛到 1 个再动手 / user 给诊断 ≠ 给修法 / 多层报错抓深层不抓表层 / framework 错误前 sanity check tensor 形状。PR #3444 online 方图 bug + PR #3611 graph mode 两个 case（B32 来源）|

> HF 模型 baseline / trust_remote_code 类的踩坑见 [`../hf/hf_alignment_pitfalls.md`](../hf/hf_alignment_pitfalls.md)。
