# Error Book: CI & 测试

## 2026-05-19 — PR #3723 streaming image edit review 漏掉协议坏路径
**症状**：审 `vllm-project/vllm-omni#3723`（`/v1/images/edits stream=true`）时，happy path 测试和 lint 基本过，但 code review 抓到三类协议/坏路径问题：(1) 新 SSE generator 用 generic `except Exception` 吃掉 `EngineDeadError`，不像已有 chat streaming 那样 `terminate_if_errored`；(2) `ErrorResponse` 在 streaming preparation 中被转成 `ValueError(prepared.message)`，400 类用户错误在 SSE error chunk 里丢状态码并默认变 500；(3) `ar_delta` replacement 分支 emit 的不是 appendable delta，客户端拼接会得到 `draftfinal answer`，测试却把这个行为固化。
**根因**：把“能把 stage-0 AR 文本和最终图按 SSE 流出来”当成“streaming endpoint 做完了”，没有把新 endpoint 当成 public protocol surface 审。review/test 主要覆盖了文本、图、DONE、单阶段拒绝，没沿着已有 streaming 实现逐项对齐 `normal chunk / structured validation error / EngineDeadError / generic exception / DONE / client append semantics`。
**解法**：review 时要求 PR 修三点：EngineDeadError 分支按既有 streaming 语义触发 server shutdown；structured `ErrorResponse` 不得降级成裸字符串异常，SSE error chunk 保留 status/type/code；`ar_delta` 必须满足 append invariant，若要支持 replacement 就改协议字段（例如 full text/reset）而不是继续叫 delta。
**对未来的提醒**：新增 `stream` 参数、SSE schema、WebSocket message、OpenAI-compatible chunk 等 API 面时，不能只跑 happy path。必须先 diff 仓库已有 streaming endpoint 的异常处理，再写坏路径测试：`EngineDeadError` 是否触发 shutdown、400 是否仍是 400、`[DONE]` 是否只在正确时机发、客户端按协议拼接后是否得到正确最终状态。凡是字段名叫 `delta`，测试必须模拟客户端 append；如果 append 不成立，字段名/协议就错了。

## 2026-05-19 — 提交前没跑 ruff，CI 被 F841 未使用变量打回
**症状**：PR CI 的 `ruff check` 失败：`vllm_omni/entrypoints/openai/serving_chat.py:2583:9: F841 Local variable negative_prompt is assigned to but never used`。
**根因**：本地只跑了 `py_compile`、focused pytest 和远端功能测试，没有跑覆盖本次改动文件的 `ruff check` / pre-commit lint。新增 streaming helper 时留下了 `extra_body.get("negative_prompt")`，功能测试不触发，但 ruff 能直接抓到。
**解法**：删除未使用变量，执行 `python -m ruff check vllm_omni/entrypoints/openai/serving_chat.py vllm_omni/entrypoints/openai/api_server.py tests/entrypoints/openai_api/test_image_server.py`，再 amend + push。
**对未来的提醒**：任何提交/推 PR 前都要跑覆盖本次改动文件的 `ruff check`；如果本地有 pre-commit 环境，优先跑对应 hook。`py_compile` 和 pytest 只能证明语法/行为，不覆盖风格和未使用变量。

## 2026-05-19 — HunyuanImage3 IT2I AR streaming PR 交付复盘
**症状**：功能实现本身完成并通过 focused tests，但交付过程连续暴露几个非功能问题：(1) 远端验证一开始没按 `docs/remote_server.md` 和 `/home/wzr` 工作区约定走；(2) PR 描述第一次按通用模板写，既不像 vLLM-Omni 真实 PR，也不好复制；(3) 提交前漏跑 `ruff check`，CI 被 F841 打回；(4) 一行 lint 修复后又默认上远端复验，撞到远端 venv 没 ruff，制造无关噪音。
**根因**：把“代码实现完成”误当成“PR 交付完成”，没有把仓库习惯、CI hook、本地/远端验证边界当成交付的一部分。远端规则和 PR 格式规则虽然后来补了，但应该在动作前先查；验证也没有按风险来源选择，出现了先不足、后过度的摆动。
**解法**：补齐并落盘四条流程约束：远端验证前读 `docs/remote_server.md`，节点 B 以 `/home/wzr` 新 worktree + 新 `.venv` 为默认；写 PR 描述前读 `.github/PULL_REQUEST_TEMPLATE.md`，必要时查线上同仓 PR；提交/推 PR 前跑覆盖改动文件的 `ruff check`；纯 lint/static 小修本地闭环，不默认上远端。
**对未来的提醒**：PR 交付 checklist 必须同时覆盖四件事：代码行为、CI 静态检查、项目真实 PR 表达习惯、验证环境选择。功能不难时更容易在这些边缘纪律上翻车；不要用“多跑远端”掩盖本地漏跑 hook，也不要用“模板三段”替代真实仓库风格。

## 2026-04-22 — GEBench test 未传 --samples-per-type
**症状**：pytest 传了参数但测试函数没透传，跑了全量数据集
**解法**：测试函数接收 fixture 并传给 `gbench_main`
**提醒**：GEBench 每样本 6 张图，smoke test 用 `--samples-per-type 1`

## 2026-04-25 — CI dummy guard 未实际执行导致 property 运行时错误
**症状**：`AttributeError: property 'device' of 'HunyuanImage3Pipeline' object has no setter`
**根因**：只跑了 `compileall`，没让新增测试函数实际执行；`object.__new__` 绕过初始化后直接写只读 property
**解法**：`monkeypatch.setattr(HunyuanImage3Pipeline, "device", property(lambda self: torch.device("cpu")), raising=False)`
**提醒**：`compileall` 不算行为验证；用 `object.__new__` 时先确认属性不是只读 property

## 2026-05-04 — "DiT-AR resize 字节相等" 测试拿 vllm-omni 自己副本当 ground truth
**症状**：写完 byte-equality 测试 PASS，但用户问"你从哪获得官方的"，发现导入的是 `vllm_omni.model_executor.models.hunyuan_image3.HunyuanImage3Processor`——vllm-omni 自己的 PR 提交记录里的副本
**根因**：写 "对齐官方 X" 测试时贪图 `from vllm_omni... import` 顺手，没确认导入的对象是否真来自模型 snapshot
**解法**：改用 `importlib.util.spec_from_file_location` 从 `$HF_HOME/hub/models--<owner>--<name>/snapshots/<hash>/image_processor.py` 加载，相对 import 用 fake parent package 注册（`sys.modules[pkg].__path__ = [snap_dir]`）
**对未来的提醒**：写 "对齐官方 X" 测试前硬性自检——「git-blame 我导入的 X，commits 是 vllm-omni 仓库的，还是 model-repo 的？」前者一律不能当 official reference

## 2026-05-04 — "AR 输出对齐"被偷懒成 "AR 输入 prompt prefill 对齐"
**症状**：用户说 "AR 输出对齐官方"，我去写 `apply_chat_template` 比 prompt prefill token id；测试还因 `HunyuanImage3TokenizerFast.from_pretrained(snap)` 实例化 fallback 到字符级 tokenizer 而 fail
**根因**：中文"对齐"两种语义都成立，input 测试 CPU 可跑、不需 GPU 看似"轻量"，偷懒掉了
**解法**：真测 AR 输出 = HF `model.generate(do_sample=False)` + omni AR 推理 + 比 generated tokens；input prefill 测试不该叫 `match_official_*` 命名（暗示 e2e）
**对未来的提醒**：用户用模糊词（"AR 输出"/"对齐"）时**默认按更难的那种解读做**（generated > input），要简化必须显式 ack 让用户确认

## 2026-05-04 — 写 IT2I AR-vs-HF 对比测试时 HF baseline 抄了 benchmark 脚本的输入
**症状**：HF baseline JSON 用 prompt=`"Describe the content of the picture."` + 随机噪声图（i2t 风格）；Omni capture 用 prompt=`"Add a cute orange cat..."` + 方块图（IT2I 风格）。两边输入对不上，token 序列对比无意义
**根因**：我直接抄了 `scripts/bench/bench_ar_hf.py` 的 PROMPT + image setup。那是个**测 AR 速度的 benchmark 脚本**，输入随便挑一个 "能跑通就行" 的；不是 IT2I 回归场景的输入。我问的问题是 "what setup runs HF AR" 而不是 "what setup mirrors the IT2I intent we're regressing"
**解法**：对比测试两侧 input 必须从**同一个 intent 描述**派生（用 IT2I 编辑 prompt + IT2I 风格条件图 + bot_task=think + sampling=greedy），不能一边从 benchmark 脚本抄一边从产品 yaml 抄
**对未来的提醒**：写比对测试前先写一句话 "本测试要 regress 的场景是什么"，然后两边 input 都从那句话派生。任何便利模板（benchmark/sample/example 脚本）的输入都要重新评估，"它能跑通"≠"它跟我的 regression intent 同一个分布"

## 2026-05-04 — IT2I yaml 已跑通仍绕去 i2t.yaml single-stage hang 8 分钟
**症状**：用户证明 `hunyuan_image3_it2i.yaml` 端到端 OK（生成猫图），我换去 `hunyuan_image3_i2t.yaml` 跑 AR-only 对比测试，那 yaml 在本环境 hang 在 orchestrator init 8+ 分钟没动
**根因**：换 yaml 前没问"我能不能在已跑通的路径上加 hook"。i2t 看起来"逻辑更干净"——美学优于实用
**解法**：保持 IT2I yaml 不变；monkey-patch `vllm_omni.model_executor.stage_input_processors.hunyuan_image3.ar2diffusion` 在 bridge 处捕获 stage 0 `engine_outputs`（AR 生成的 cumulative_token_ids）
**对未来的提醒**：用户说"X 已跑通"后，**不能在不显式解释为什么换的前提下绕路**。换路径 = 承担新路径全部 init/dep 风险，「代码整洁度」对用户没有价值

**症状**：`AttributeError: property 'stage_durations' of 'HunyuanImage3Pipeline' object has no setter`
**根因**：`stage_durations` 只读 `@property`，getter 依赖 `_profiler_lock`（只有 `setup_diffusion_pipeline_profiler` 才初始化）；`object.__new__` 裸实例两个问题叠加
**解法**：加 `@stage_durations.setter`（懒初始化）；getter 加 `hasattr` 守卫
**提醒**：新增 Mixin property 先问：测试能不能直接赋值？这是同类问题第二次

## 2026-05-08 03:30 — 拿到"测一下 PR #3055"任务，自己手写 end2end 调用脚本而不用 PR 自带 pytest 用例
**症状**：用户给了 47.79.124.13 节点 + "/mnt 模型 /rebase 环境 + PR #3055 出图打分有问题去测"。我把 PR #3055 当成"加 buildkite job"理解，clone main 后自己手写 `/tmp/run_hi3_t2i.sh` 调 `examples/.../end2end.py --modality text2img`，连续踩坑：
  1. `--stage-configs-path hunyuan_image3_t2i.yaml`（裸文件名）→ FileNotFoundError，error message 自带迁移指示「Legacy `stage_configs/` yamls were replaced by `vllm_omni/deploy/<model>.yaml`; use `--deploy-config`」我没读，又拼了一次绝对路径继续硬塞
  2. 第二次硬塞绝对路径加载成功，但 4 worker 在 4 卡上各自吃 ~110GB（不是真按 TP=4+EP 切），炸 OOM
  3. 我开始分析"DiT 80B 是不是 4×143GB 装不下"——用户怒了：「PR #3055 这个 PR 就是给用户一键跑测试的，你为什么直接写脚本，浪费我 token」
**根因**：
  - 没把 PR #3055 当成**入口**而当成**配置增量**。PR 里 `tests/e2e/accuracy/test_gebench_h100_smoke.py` + `--gebench-extra-server-args` JSON + `--gebench-stage-overrides` JSON 已经把"如何起 server / 怎么传 dtype / TP / EP / executor backend / async chunk"全配好了，pytest 一行带完。我自写脚本用 `Omni()` 入口，把这些已知好的参数全部丢了，必然踩坑。
  - 用户在前一轮跟我聊的就是"这个 PR 的 CI 步骤"——`.buildkite/test-nightly.yml` 里那条 `pytest -s -v tests/e2e/accuracy/test_gebench_h100_smoke.py --gebench-model tencent/HunyuanImage-3.0-Instruct ...` 是 ground truth。我把这条命令从 buildkite 删了之后，**完全忘了那条命令本身就是怎么跑这个测试的说明书**。
  - FileNotFoundError 的 error message 自带"用 --deploy-config"指示，我没读 message 直接 sed 绕路。
**解法**：直接用 PR 的 pytest 用例。git checkout PR 分支后：
```bash
pytest -s -v tests/e2e/accuracy/test_gebench_h100_smoke.py \
    --run-level full_model \
    --gebench-model tencent/HunyuanImage-3.0-Instruct \
    --accuracy-judge-model QuantTrio/Qwen3-VL-30B-A3B-Instruct-AWQ \
    --gebench-devices 0,1,2,3 --accuracy-gpu 0 --gebench-port 8094 \
    --gebench-samples-per-type 2 --gebench-num-inference-steps 28 \
    --accuracy-workers 1 --gebench-t2i-only \
    --gebench-stage-overrides '{"0":{"devices":"0,1,2,3","enable_expert_parallel":true,"max_num_seqs":1}}' \
    --gebench-extra-server-args '["--dtype","bfloat16","--gpu-memory-utilization","0.95","--enforce-eager","--trust-remote-code","--distributed-executor-backend","mp","--no-async-chunk"]'
```
4×L20X 143GB → loaded 57GB/卡 PASS in 7m10s；artifacts 在 `tests/e2e/accuracy/artifacts/gebench_<model>/`（PNG + summary.json + evaluations/type*.json + reasoning）
**对未来的提醒**：
  1. 接到「测一下 PR」任务时**先问**：PR 是在加测试用例（pytest entrypoint）还是只加 CI step？前者直接 pytest 命令照搬，禁止重写 inference 入口
  2. 如果 PR 加了 buildkite/CI step，**那条 step 的命令本身就是"如何跑这个测试"的官方文档**——把它从 CI 删了之前先在 memory 里记住命令，删了之后还能回去拷
  3. error message 含「use X instead」「replaced by Y」「migrate to Z」之类**显式迁移指示**时，先按 message 试一遍，再考虑 workaround；不要 sed 绕路
  4. 自写 `Omni()` / `LLM()` 调用脚本之前自检：现成的 `tests/` / `benchmarks/` 里有没有同任务的 entrypoint？有就用现成的，没有再写
  5. PR #3055 GEBench 跑 4 个样本（type3+type4 各 2）只要 ~7 分钟，不是「重活」——用户给一个能用 7 分钟 pytest 跑通的活，我用 30 分钟 + 多次 OOM 没跑出来。"看起来我的方法更通用"是错觉，**和官方测试框架对齐永远是首选**

## 2026-05-08 — 把 PR scope 内的"功能门"误读成"测试盲点"，建议跑 PR scope 外的路径
**症状**：测 PR #3055 时，`--gebench-t2i-only` flag 让 type3/type4 trajectory 只生成 frame0。我把这个观察包装成"测试只 cover 第 1 帧，缺了 logic/cons/goal 三个核心维度，应该去掉这个 flag 跑全 6 帧 trajectory"，劝用户重跑 IT2I 路径。用户怒：「我要 --dit-only」「智力太差，记一下」
**根因**：PR #3055 第一个 commit `8ee36c49` 已经写明：
  - `pipeline_registry.py: register HUNYUAN_IMAGE3_DIT_ONLY as default for HF model_type "hunyuan_image_3_moe"`
  - `pipeline.py: DIT_ONLY topology (pure T2I path, no AR stage)`
  - `gbench.py: add --t2i-only flag (skips IT2I edits in generate and evaluate; type1/2/5 are out of scope until the AR->DiT bridge lands)`
  整个 PR 就是 **DiT-only 单图测试**——`--gebench-t2i-only` 不是"偷懒少测"的开关，是**这条 PR 的核心定位 flag**。我读了 commit message 还把它定性成"覆盖盲点"建议跑 trajectory，等于劝用户做 PR-scope-out 的 IT2I 测试，那条路在这个 PR 里**根本没接通**（pipeline 是 DIT_ONLY topology，server 没起 AR stage，跑 trajectory 必失败或 silently fallback）。
**解法**：保留 `--gebench-t2i-only`，按 PR scope 跑 DiT-only 单图，调步数解决质量问题
**对未来的提醒**：
  1. 测一条 PR 之前先读它的**首个 commit message**——那里通常写明 PR scope 边界（"X out of scope until Y lands"），任何越界建议都是错的，哪怕看起来"更全面"
  2. PR 自带的 flag 命名往往**就是 PR 定位的快捷读法**：`--gebench-t2i-only` 字面就是"只测 T2I"——这不是限制，是 PR 边界。flag 名字像"only/skip/disable"开头时不要本能地想"我帮你打开它跑全套"
  3. PR scope 内的"测试覆盖不全"是**已知主动决策**（commit body 一般会写"defer to next PR"），不是 reviewer 该补的盲点
  4. 用户说"再跑一次看看"默认按**同 scope、改一个变量**重跑（这次：step 数 28→50），不要顺手把另一个变量也改了——一次只动一个
  5. 这条出现的二级错误：开始 grep DIT_ONLY 想"探查能不能强行跑 IT2I 拓扑"——已经在 PR-scope-out 路上又加挡。看到 commit message 写 scope 边界后**应该立刻停手回到 scope 内**，不是研究怎么破墙

## 2026-05-08 — PR #3332 review 三连：把 exploration-mode 残留带进了独立 smoke test PR

**症状**：PR #3332 (`feat/hunyuanimage3-i2t-ar-prefix-ci`) 只加一个文件 `tests/e2e/offline_inference/test_hunyuanimage3_i2t_expansion.py`，被 reviewer 指出三处问题：
  1. 注释里引用 `scripts/bench/hf_i2t_pr2986_baseline.py` / `scripts/bench/baselines/hf_i2t_pr2986.json` / `memory/hf/hf_omni_alignment_method.md` —— 这三个文件在仓库里**根本不存在**（在我本地工作分支 / 计划中的 follow-up，但没进这条 PR）。
  2. `from PIL import Image` 写在测试函数体里，没提到顶部 import 块。
  3. `request_output = getattr(first_output, "request_output", first_output)` —— `Omni.generate()` 返回类型已经是 `list[OmniRequestOutput]`，`request_output` 属性在 `vllm_omni/outputs.py:58` 明确定义；这个 getattr fallback 在 API 改名/删字段时**静默**返回错误对象继续跑，掩盖回归。

**根因（共同体）**：从更大的探索/调试会话里**抽小 PR**，没做"如果只看这条 PR，这段代码读起来合理吗"的审计。三处都是 exploration-mode 模式残留：
  - **悬挂引用**：写注释时本地工作树里 `scripts/bench/hf_i2t_pr2986_*` 和 `memory/hf/hf_omni_alignment_method.md` 都在，注释自然地指向它们。抽 PR 时只把测试文件 cherry-pick 出来，文件链路断了，注释成了"指向虚空"的脚注。
  - **lazy import**：探索期 `from PIL import Image` 放函数里是为了 test discovery 阶段不引入 PIL（怕环境缺包导致 collect fail）；但既然已经 `import torch`，环境必然有 vision stack，lazy import 没价值，只是 exploration 期保守姿态没擦掉。
  - **defensive getattr**：写测试时不确定 `outputs[0]` 是 `OmniRequestOutput` 还是裸 `RequestOutput`（探索期同时在跑两条对比脚本，一条是 vllm-omni 一条是 HF），所以加了 fallback。等抽进 PR、明确这条路径走 `Omni.generate()` 时，应该裸属性访问；fallback 留下来变成静默掩盖工具。

**解法**：commit `5c19158e` —— 删悬挂引用、PIL import 上提、`outputs[0].request_output` 裸访问。

**对未来的提醒**：
  1. **抽小 PR 时跑一次"只看这条 PR"的审计**：`git show <commit> --stat | git show <commit>` 整段读一遍，自问"如果这是别人的 PR，我会不会问 X 在哪 / 为什么这样写"。注释里所有跨文件引用必须 grep 确认引用目标在这条 PR 的 base+diff 里。
  2. **defensive getattr / hasattr 在测试代码里是反模式**：测试的本职是"API 不符合预期就立刻报错"，silent fallback 反过来掩盖回归。只有写**通用工具代码**且 API 故意宽松时才用，测试代码一律裸属性访问、裸索引、裸 cast。
  3. **lazy import 只在两种场景成立**：(a) 真有 optional dep（`try: import X except ImportError: ...`）；(b) 启动时间敏感的 CLI 入口。普通测试文件别 lazy import——会被 reviewer 当作"代码组织没整理完"。
  4. **写测试注释引用外部文件之前先想"这个引用在 PR landing 半年后还成立吗"**：内部脚本路径会被 rename / 删除 / 移到 archive，引用会变烂注释。如果想留 trace 用 commit SHA + 一句话语义解释（"verified bitwise match against HF greedy"），比文件路径更稳。
  5. 这条 review 的 meta lesson：**抽 PR 是一次重新审视代码的机会，不是"复制粘贴 + push"**。从大工作树往独立 PR 抽时，本能上不再读代码，是错觉——base 上下文变了，原本合理的写法可能变成废墟。

## 2026-05-08 — GEBench Qwen3-VL judge 给"几乎空的图"打 5/5 满分
**症状**：HunyuanImage-3.0 T2I 出 4 张图（type3+type4 各 2 张，prompt 都是"chinese_computer"）：
  - sample_0001：模糊乱码 UI 截图，judge 给 logic/qual/ui/cons=2, goal=3，overall 0.44，reasoning 准确指出"low-quality, blurry, illegible text"
  - type4 sample_0002：**几乎全黑画面中央一个白色矩形**（明显坍缩），judge 给 5/5/5/5/5 满分 1.0，reasoning：「accurately fulfills the instruction to 'generate an image' with **no specific content requirements**. The composition is logically consistent...」
  - type3 sample_0002：满分 1.0，reasoning 类似"sharp and artifact-free"
**根因**：判官 LLM 在 prompt 没明确视觉要求时把"画面干净/无 artifact"当成满分依据，对**坍缩成空白图的 mode failure 完全识别不出**。判官给的是"图本身是不是 well-formed"而不是"图是否完成 instruction"——但 instruction 又因为太抽象（"chinese_computer"）让判官退回到"无要求即满足"。最终 score 0.72/1.0 严重高估，掩盖了一半样本是坍缩输出。
**解法**：本次只是观察，未修。可能方向：(a) judge prompt 加 "if image is blank/near-uniform, automatic fail"；(b) 加 image-stat sanity check（std<阈值就 0 分）；(c) GEBench 数据集 prompt 改成有具体视觉锚点，避免"generate an image"这类模糊命令落入判官 lazy fallback
**对未来的提醒**：
  - 看 GEBench 综合分（overall_mean）之前先 grep 单样本 raw_scores 看分布，**全 5 + 全低分混合 mean 出 0.72 是可疑信号**，不是"中等水平"
  - judge LLM reasoning 字段必读，包含 "no specific content requirements" / "abstract composition" / "blank" 等措辞 → 判官在打 cargo cult 满分
  - 单边 judge 分不能当 quality 证据（与 B9 共鸣）；用户说"出图打分有问题"时第一动作是看图本身，**不是看综合分**
