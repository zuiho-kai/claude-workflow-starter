---
name: reviewer-lens-audit
description: 自审 / sub-agent review 必跑的 4 条 reviewer-perspective audit。Sub-agent 说"OK"是弱信号——它只会答你问的那个问题。
metadata:
  type: feedback
---

# Reviewer-lens audit：4 条必跑清单

**Why：** PR #3626 review iteration——我 push 前让 sub-agent code check 说"no problem"，TaffyOfficial reviewer 一上来 4 条评论：算法重复 3 份、resolution 算在错的层、token id 非连续段没处理、help text 冗余。**用户原话："这是严重问题，你要学习从 review 角度去看问题。code check 他护不住，容易被打回。"**

派生自 [review_delegation_framing](review_delegation_framing.md)——那条管"怎么 spawn"，**这条管"必须审什么"**。CLAUDE.md B33 是硬规则入口。

---

## 🚫 禁用 framing（这些 prompt 直接换掉）

下列任意一句 = 子 agent 必答 "no issues found / looks OK"，**护不住** reviewer：

- "帮我 code check 一下"
- "看有没有问题"
- "review 一下这个 PR / commit / 改动"
- "static review 看下"
- "扫一遍" / "审一下"
- "确认一下没问题"

**Why**：子 agent 严格在 prompt 框定的范围内答；没给 audit 维度 = 它没有判定 "出问题" 的标尺，默认走"看起来合理就 OK"。

**替换**：用下面的 4-audit 模板，或把模板拆 3 份并行（duplication / layering / edge+surface）。

---

## ✅ Sub-agent prompt 模板（直接粘贴用）

```
Static review this PR/diff/change. For EACH of the four audits below, return
findings (P0 blocker / P1 should-fix / P2 nit) OR explicitly write "none found"
— do not skip any audit and do not pre-focus on one over another.

# Audit 1 — Duplication
Grep both the repo (`vllm_omni/`, `scripts/`, etc.) and the upstream reference
repo for functions / classes / algorithms / constants that overlap with anything
new in this PR. List each match with:
  - file:line of the existing implementation
  - file:line of the new implementation
  - 1-line judgment: should reuse / cannot reuse + why

# Audit 2 — Layering
For each new piece of logic, identify which module persistently holds the data
it operates on. If logic and data live in different modules (e.g. resolution
done in CLI/serving but data in Processor), list as a finding with:
  - new logic location
  - data owner location
  - proposed correct home

# Audit 3 — Edge cases
List every range / boundary / default value the new code touches. For each,
name which branches handle:
  - empty / single-element / max-size extremes
  - non-contiguous ID ranges, off-by-one (range(s, e) vs s..e inclusive)
  - None vs 0 vs sentinel (which branch does "not provided" take?)
  - feature-flag matrix: enabled/disabled flags crossed with old/new execution
    modes (for runner/cache changes: cache on/off, hit/miss, last/non-last PP
    rank, downstream all/subset, and payload/no-payload requests)
Flag any boundary not explicitly handled.

# Audit 4 — Surface area
List every new public knob (CLI arg / API field / extra_args key / config
option / new public function / SSE or OpenAI-compatible response chunk). For each, answer:
  - If this is a request parameter, extra_body/extra_args key, processor kwarg,
    multimodal key, or cross-module bridge field, provide a contract matrix:
    ingress path(s), allowed value shapes, normalization point, owner module,
    downstream consumer(s), no-op cases, docs, and tests.
  - Can it be derived from existing knobs? If yes, why expose it?
  - Why is the default what it is? Can the help text be shorter?
  - Is the same value also expressible via another path (CLI vs env vs config)?
  - If this is a public API field or response schema, where is the protocol type
    defined, where is it documented, and what bad-path tests cover it?
  - If this is streaming/SSE/WebSocket, which existing endpoint pattern and
    output-processor mechanism does it reuse? If it hand-rolls delta/error/DONE
    semantics, flag it.
  - If this is an internal optional fast-path parameter, what are its data
    contract and execution-context contract, and where does a wrong caller fail?
  - If this changes a shared state/schema type, list every constructor, unpack
    site, and consumer found by grep, and state how positional arity remains
    compatible.
Flag knobs that are accreted/over-defensive.

Return findings in markdown. End with one line: "AUDITS RUN: 1,2,3,4 — N findings (Pa P0, Pb P1, Pc P2)".
```

### 输出必须先说人话

reviewer-lens 可以用 P0/P1/P2，但每条 finding 必须先回答三件事：

1. 会发生什么坏事。
2. 为什么这是当前 PR 要管的事。
3. 最小收口是什么。

禁止只写 `contract` / `ABI` / `surface area` / `state matrix`。这些词只能当括号里的精确标签，前面必须有具体行为例子。

例：不要写“piecewise attention contract 不清”。要写“如果 mask 里有某个 query 不能看某个 key，当前压缩会把这个禁看关系丢掉，token 会看到不该看的 token；所以只允许 padding 行/列，其他 mask fallback 或 raise。”

### 新模型接入追加模板：双 owner 审核

新模型 / 新 pipeline / 新 backend PR 不能只问“有没有问题”。**第一次 push 前**至少开两种 reviewer framing；reviewer 提醒后再补跑只能算补救，不算合格首轮自审：

```text
Role A: module owner. Review semantic parity against upstream. Treat shape-clean
and strict load as weak evidence. Check scheduler / denoising loop, embedding
order, activation, token order, special token + pad/eos attention mask,
preprocess, noise/action contracts, and real-checkpoint fail-fast behavior.
Return P0/P1/P2 findings only.

Role B: omni project owner. Review whether this integration matches repo
architecture. Check file/module ownership, public API surface, test placement,
stub-vs-real evidence separation, PR body reproducibility, and whether any
generic helper leaks caller-specific semantics. Return P0/P1/P2 findings only.
```

**规则**：Role A 管“像不像 upstream”，Role B 管“像不像 vllm-omni”。两者都通过，才算 reviewer-lens audit 有效；其中任一方只看 shape / smoke 都不算完成。这个 gate 必须发生在首个公开 push / PR 创建前，而不是等 reviewer 指出来再补。

### 开发前 mini spec：不要把 review 当第一道语义检查

非平凡 vLLM-Omni 改动在写代码前必须先写一个短 mini spec。触发条件：

- 新模型 / 新 pipeline / 新 backend 接入；
- normal `forward()` 之外新增 step / graph / cache / batching / serving / offline / benchmark 路径；
- 新增或修改 public API、CLI、`extra_args`、`mm_processor_kwargs`、multimodal key、AR↔DiT bridge 字段；
- 修改 scheduler、decode、VAE latent、KV/cache、batch expansion 语义；
- PR 需要写性能提升或远端验证证据。

mini spec 必须短，但要覆盖这四块：

```text
Mini spec
- Goal:
- Changed surfaces:
- Field contract:
  - ingress:
  - default semantics:
  - owner:
  - consumers:
  - failure policy:
- Path parity matrix:
  - normal path:
  - variant paths:
  - shared helper or intentional split:
- Non-default tests:
- Validation and PR evidence:
- Explicit non-goals:
```

字段契约要列到 consumer，不是只列 parser。尤其要区分用户默认、tokenizer/processor 默认、system prompt 默认、scheduler/RoPE 默认、decode 默认、KV/cache/backend 默认；不同 consumer 需要不同默认值时，必须拆变量，不能一个 normalized value 到处传。

路径矩阵要把 normal path 和所有变体逐行对齐：step execution、graph/cache、T2V/I2V、direct arg vs prompt dict、image vs latent、packed vs unpacked、offline vs serving。两条路径如果解析同一套请求语义，必须共用 owner helper；复制 parsing / normalization 直接按 bug 处理。

测试计划必须包含非默认字段。默认 smoke 只能证明 plumbing，不能证明语义。常见必测项包括：非默认 fps/frame_rate、`num_outputs_per_prompt > 1`、prompt dict fallback、direct arg path、list/batch 输入、provided latents path、conditioning token / first-frame preservation、string bool / `None` / sentinel。

PR evidence 要在开发前定好口径：哪些能本地证明，哪些需要远端，哪些性能 claim 需要同 workload baseline。PR body 的功能验证必须对应当前 PR head；性能数据如果来自较早 checkout，必须明确标注，不能暗示在最新 head 重跑。公共 PR 文案不能写本地个人路径、远端 host/user/path、cache 探测失败或本地缺依赖 blocker。

**规则**：mini spec 写不出来，不准开始编码。后续 sub-agent review 只兜底，不能替代这一步。若 mini spec 看起来太重，说明改动应该能用五行讲清；五行也讲不清，就必须写 spec。

### 修改方案前：双 owner 设计审核

非平凡业务改动不能等代码写完才开 sub-agent。开始想“怎么改”、准备定方案或写第一版代码前，先开两个 owner framing：

```text
Role A: module owner. Given the user request and relevant current code, propose
how this module should be changed before implementation. Identify the owning
module/data boundary, required contracts, state matrix, edge cases, and tests.
Return P0/P1 risks in the proposed approach, and name the simplest acceptable
implementation shape. Do not review an already-written patch.

Role B: omni project owner. Given the user request and relevant current code,
review the intended change at repo level before implementation. Check whether
the change belongs in this module, whether it expands public/internal surface,
whether it needs docs/PR evidence, and what validation matrix protects other
pipelines/backends. Return P0/P1 risks and the smallest repo-aligned plan.
Do not review an already-written patch.
```

**触发**：runner / prefix cache / shared execution state / pipeline / public API / 新模型 / batching / streaming / 多模块 ownership 变化。纯 typo、格式、无行为文档改动可跳过。两个 owner 的 P0/P1 必须进入方案后再动手；不能把事后 audit 当补救。

---

## 规则

**触发**：想方案前 + 自己 push 前 + spawn review sub-agent 时。

**Sub-agent OK ≠ clean PR**。子 agent 只严格在 prompt 框定的范围内审，**没问到的它不会主动说**。每次开 PR / 自审都必须显式跑这 4 条 audit，不论自己跑还是 union sub-agent。

### Committer pre-review framing：不要只审模块语义

当用户说“预期不要让 committer 有其他意见”或准备请求 merge 时，module-owner 审核不够。必须额外开一个 **omni project owner / committer pre-review** framing，显式检查：

- public API / `extra_body` / `extra_args` / `mm_processor_kwargs` 的完整 contract matrix；
- endpoint 层 structured error，而不是只看 helper-level `ValueError`；
- 测试是否放在行为 owner 文件，不能只找“相关”文件；
- PR body / Test Plan / Test Result 是否和当前 head、当前测试面一致；
- 当前 unresolved / non-outdated reviewer thread 是否还指向有争议的代码。

**PR #3626 三次反例**：第一次只让 sub-agent 偏模块语义看 HunyuanImage3 explicit size / AR ratio，没问 committer surface，于是漏掉 `/v1/images/generations` T2I prompt-side `mm_processor_kwargs["infer_align_image_size"]` 仍会把文本请求切到 multimodal processor path；也漏掉 PR body/Test Result 已过期。第二次用 committer framing 才抓到这些问题。

**规则**：module owner 只说明“这段模型语义是否对”；committer owner 才会问“这个公开面、测试归属、PR 文字、坏路径是否能 merge”。两种 framing 缺一项，不能把 sub-agent “no P1”当成可 push 结论。

### Fix 后必须复审修复 diff

处理完 sub-agent finding 后，要把**新产生的 diff**再发回同样的 reviewer framing，问题必须是：

```text
Prior findings 是否真的 resolved？
这次修复有没有引入新的 API/test/PR-body surface？
只返回 P0/P1/P2 或 no further findings。
```

**PR #3626 反例**：第一次发现 packed routing 测试不该放 sampler 后，只把它挪到 fused MoE 文件；但行为 owner 其实是 AR/model-executor routing helper，第二轮才挪到 dedicated `test_hunyuan_image3_routing.py`。修复 finding 不等于 owner 正确，必须复查修复 diff。

### Full diff review 不是 issue-closure review

当用户要求“全量 diff / 项目级 review / 看有没有垃圾修改 / 1800+ 行太大”或准备 push/PR 时，不能只复查已知 reviewer finding。必须先生成并在汇报里引用这三件证据：

```powershell
git diff --stat origin/main...HEAD
git diff --name-status origin/main...HEAD
git diff --numstat origin/main...HEAD
```

必跑三段：

1. Diff census：按新增行数排序，列 top files、owner、为什么属于本 PR、是否可能拆出。
2. Semantic trace：每个新增 helper / dataclass / parser / scheduler / docs default 必须追到 public consumer：normal forward、variant forward、serving/offline entrypoint、test。只测 helper 输出不算通过。
3. Garbage pass：专门找重复逻辑、tensor-valued `or` / silent fallback、未使用 public knob、docs/perf overclaim、只测 unit 内部不测入口、同类 bug 横向漏扫。

输出必须包含：

- `DIFF REVIEW BASE: <base>...<head>`
- `TOP FILES REVIEWED: ...`
- `AUDITS RUN: diff-census, semantic-trace, garbage-pass, reviewer-lens-1..4`
- `KNOWN FINDINGS CLOSED != FULL DIFF CLEAN`，除非上面三段全部执行。

**规则**：sub-agent 只问“之前那几个问题是否 resolved”只算 finding closure，不算 full-diff review；不能用“没有 P1/P2”描述整个 PR。只要没跑完整 gate，汇报必须写 `known findings closed`，不能写 `full PR reviewed` / `clean`。

**PR #4381 反例**：LTX-2.3 适配前几轮只围绕 checkpoint/docs/perf 已知 finding 收口，没有跑 full diff census + semantic trace，所以漏了 `prompt_embeds` helper 输出在公开路径被 `check_inputs()` 拒绝、I2V tensor-valued `or` fallback 会炸、recipe/perf workload 描述不匹配。以后这类漏项按 full-diff gate 缺失处理，不再归因于 reviewer 没问到。

### Sub-agent finding 先做 scope triage，不能直接编码

Sub-agent 提到某个相邻模块会受影响时，先判断它是**root-cause owner**还是**downstream symptom**。只有 root-cause owner 才能直接改；downstream symptom 默认通过修 shared/source owner 解决，不能先给下游模型加 defensive patch。

**每条 P0/P1 finding 落地前必须补 4 个答案：**

- Root cause owner 是哪个文件/函数？证据是 source grep、reviewer comment anchor、还是测试失败？
- 最小修复文件集是什么？新增一个无关模型文件时，为什么不能只修 source owner？
- 这是不是当前 PR 必需？删掉这个修复，当前 reviewer comment / 主线行为还会坏吗？
- 测试应该放在哪个 behavior owner？如果只是为 defensive patch 新增测试，patch 删除时测试必须一起删除。

**PR #3626 反例**：sub-agent 看到 Bagel 依赖 `multi_modal_data["img2img"]`，这个 finding 本身是对的；错误在执行层把它转成 `bagel.py` sanitizer patch 和 Bagel 专用测试。实际 root cause 是 shared `serving_chat.py` 把 chat-completions img2img payload 改成 `{"image": img}`，最小修复是把 shared path 恢复 `{"img2img": img}`，并用 serving 层回归测试保护 key 不再被改。Bagel 文件没有当前 PR 必需的行为变化，不能带进 diff。

**规则**：sub-agent finding 的默认动作不是“按它提到的文件加代码”，而是先写一句 scope conclusion：`root owner = X; downstream affected = Y; current PR patch = X only; test owner = Z`。写不出来就先不改代码。

### Rebase 后必须跑 fresh reviewer-lens

rebase / cherry-pick / conflict resolution 后，之前的 sub-agent audit 和人工自审只对旧 head 成立；新 head 是新的 diff。不能用 `ruff` / `compileall` / `git diff --check` 代替语义复审。

**必须复审三类文件：**

- conflict 文件：手动选过哪边，就按新代码重新审 owner / edge / surface。
- auto-merged 文件：Git 没报冲突不代表语义没被回退，尤其是同一函数里两边各改不同段。
- 当前 non-outdated reviewer threads：reviewer 新评论锚点必须按最新 head 重读；outdated thread 可参考但不能当当前问题列表。

**最小 gate：**

```powershell
git range-diff <old-base-or-old-head>...<old-head> origin/main...HEAD
git diff --stat origin/main..HEAD
git diff origin/main..HEAD -- <conflict-or-auto-merged-files>
gh pr view <PR> --json headRefOid
```

然后按 reviewer-lens 4 audit 问：

- 主干已有语义有没有被“修复”覆盖掉？例如 HunyuanImage3 explicit size 同时有两个 contract：`image_size` 传给 `resolve_stop_token_ids()` 决定 AR stop 位置；`target_h` / `target_w` 传给 sampler 决定强制哪个 ratio token。只保留 `target_h/w` 就是 revert 主干 stop-token contract。
- 共享路径有没有被模型专属规则污染？例如 `multi_modal_data["image"]` 对 HunyuanImage3 DiT 是正确 consumer，但 Bagel 的 parser 依赖 `multi_modal_data["img2img"]` 走 img2img processor。共享 chat path 改 key 前必须 grep 所有 model parser / pipeline consumer。
- reviewer 已经问“why revert previous change?”时，默认不是解释问题，而是 bug detector：先 `git show origin/main:<file>` 看主干锚点附近原语义，再决定修复。

**PR #3626 三次反例**：rebase 后 `end2end.py` 丢了 `resolve_stop_token_ids(..., image_size=ar_image_size)`，导致 explicit `--height/--width` 仍按 auto ratio stop；同时把 chat completions shared img2img payload 从 `{"img2img": img}` 泛化成 `{"image": img}`，会影响 Bagel。前几轮 audit 只看 HunyuanImage3 infer-align / explicit size 目标，没有在 rebase 后重跑 shared-path committer audit，所以漏掉。

### Contract matrix：public API / extra_args / multimodal bridge 必列

新增或修改以下任意一个，都不能按“一个 caller 里看起来能跑”处理：

- OpenAI-compatible request 参数、`extra_body`、`extra_args`
- `mm_processor_kwargs`、processor kwarg、pipeline extra body
- multimodal key（如 `image` / `images` / `img2img`）
- AR↔DiT bridge、serving→engine prompt、pipeline→processor 字段
- CLI/example 暴露出来的模型行为开关

动手前必须写这张矩阵：

| Column | 必答问题 |
| --- | --- |
| Ingress | top-level field / nested `extra_args` / CLI / example / legacy caller 哪些入口能表达同一个值？ |
| Value shape | `True`/`False`、`"true"`/`"false"`、`None`、0/1、sentinel、缺省分别怎么走？ |
| Normalization | 哪一层唯一负责 parse/normalize？是否禁止下游再 `bool(value)`？ |
| Owner | 谁拥有语义：serving/protocol、AR bridge、DiT pipeline、processor、model config？ |
| Consumer | 下游实际读哪个 key / field？旧 key 是否兼容？unsupported path 是 fail fast 还是 documented no-op？ |
| No-op cases | 例如 T2I 没有 condition image、feature disabled、empty image list 时是否显式说明？ |
| Docs/tests | docs、protocol/schema、bad-path test、legacy-key test、string-bool test 在哪里？ |

**PR #3626 二次反例**：`infer_align_image_size` 被当成局部 image-size 参数看，漏了两条 contract P1：

- `/v1/images/edits` 单图路径写入 `multi_modal_data["img2img"]`，但 AR→DiT bridge / DiT `pre_process` 主路径只消费 `image` / `images`，条件图可能静默丢失。
- top-level 参数用 helper parse 了 bool，但 nested `extra_args` raw-merge 到 pipeline，`bool("false") == True` 让用户显式传 `"false"` 反而启用。
- T2I/generation 没有 condition image，`infer_align_image_size` 对 prompt-side image processor 是 no-op；但只要把它塞进 `mm_processor_kwargs`，`OmniInputPreprocessor` 就会走 multimodal processor 路径。正确 contract 是：T2I 可继续通过 diffusion-stage `extra_args` 表达 flag，但不要仅因这个 flag 注入 prompt-side `mm_processor_kwargs`。

**规则**：contract matrix 缺任一列，sub-agent “OK”无效；这种 finding 必须按 P1 处理，不能降级成 reviewer nit。

### Inline review 处理：锚点代码是 source of truth

处理 GitHub inline review 时，**评论文字不是唯一输入，锚点代码才是 source of truth**。每条评论动手前必须先写出 action mapping：

```text
Comment: <reviewer 原文>
Anchor: <file:line + 锚点代码实际行为>
Pronoun target: <this / it / here / strategy 指向锚点里的哪个实体>
Reviewer asks: <按锚点语义拆成 1-3 个具体要求>
Code action: <要改哪个 owner/module，什么逻辑从哪里移到哪里>
Done check: <回到锚点附近看 diff，reviewer 是否会认为正面解决>
```

**禁止按关键词修评论。** 看到 "image processor" 不等于随便搬一个相关 helper；看到 "add comments" 不等于只加 docstring。先问：reviewer 评论锚在哪几行？这些行的行为是什么？`it` / `this` / `strategy` 默认指锚点里的最近代码实体，而不是上一条评论、相邻概念、或自己脑中相关的模块。

**PR #3626 反例**：Bounty-hunter 的评论锚在 `pipeline_hunyuan_image3.py` 的 output alignment/postprocess resize：

```python
scale = math.sqrt(target_area / (ori_width * ori_height))
new_w = round(ori_width * scale)
new_h = round(ori_height * scale)
outputs[batch_index] = output_image.resize(...)
```

评论说 "Add comments to explain the alignment strategy ... And also add it to image processor?"。第一次只把 condition-image `_resize_and_crop` 搬进 image processor + 给 pipeline postprocess 加 docstring，是**按关键词修**，没有按锚点修。正确 action mapping 应该是：把 output alignment strategy / `_postprocess_infer_aligned_outputs` 放到 `HunyuanImage3ImageProcessor`，pipeline 只调用 processor method。

**Done check**：改完必须回到原评论锚点附近看 diff。如果锚点附近的核心逻辑仍留在原 owner，只是旁边多了注释或改了相邻 helper，不能算完成。

### Audit #1：Duplication（已经有了吗？）

新增的函数 / class / 算法 / 常量，**先 grep 仓库 + 已 clone 的 reference repo**，看有没有同概念实现：

```bash
grep -rn "<function-name-or-concept>" vllm_omni/ scripts/ <upstream_repo>/
```

返回非空 → 必须答"为什么不 reuse"，写不出答案就 reuse。

**典型信号**：你的新函数名跟某处现有函数 80% 重合（`_calc_by_step` vs `_build_reso_group_ratios`）、algorithm 描述能完整复刻另一处的 docstring、参数列表镜像现有 class method。

### Audit #2：Layering（这逻辑住对地方了吗？）

新逻辑需要的数据 / 状态在哪持有？**逻辑就该在哪**。

- entry point（CLI / serving 层）做了本该在 model / processor 里做的解析 → 错层
- 把数据序列化成"不透明 token"传给下游（PR #3626 的 `target_ratio_idx`） → 信号：下游需要的不是这个 token，是原始 (h, w)
- "lightweight 模块不能依赖 heavy 模块"是真约束，但解法是**把代码搬到 heavy 模块那一层**，不是**在 lightweight 模块再造一份**
- generic helper 的参数名带着某个 caller 的专有概念（例如 tensor merge helper 里叫 `hidden_states_cpu`）→ helper 抽象层级和命名层级不一致

**问自己**：把这段代码 cut，paste 到 X 模块里能不能直接跑？能跑就该住那。

### Audit #3：Edge cases（非连续 / 边界 / off-by-one）

这是 reviewer 不会明说但会指出 bug 的地方。**主动查**：

- 看起来连续的 ID range 真的连续吗？（PR #3626：`<img_ratio_0..32>` 是 128044-128076，`<img_ratio_33..36>` 跳到 130103-130106——一个 `start + idx` 的算式覆盖不了两段）
- 默认值 None vs 0 vs sentinel 的边界（"没传"和"传了 0"哪个走哪条分支）
- list / set / range 的 ±1 边界（`range(s, e)` 含 s 不含 e，`s..e` 通常含两端）
- empty / single-element / max-size 三个极端
- continuous/dynamic batching 改动要把 request-local state 拆开审：tensor shape、非 tensor metadata、request index 映射、CFG branch、slice/offset、KV/attention metadata 是否都能合批再拆回；`full_attn_spans` 这种随 prompt length 变化的字段，shape padding 过了也可能让 backend 语义不成立
- grouped batching 的 edge input 不能只用 duplicate prompt；至少问一次：不同 prompt length、不同 request state、`max_concurrency/max_num_seqs > 1` 时是否真的命中 grouped path
  - runner / prefix-cache / pooler payload / shared execution state 改动要列状态矩阵，尤其是 feature flag x cache mode：cache on/off、prefix hit/miss、`requires_full_prefix_cached_hidden_states` true/false、downstream req all/subset、last/non-last PP rank、staged CPU tensor None/fallback、deferred multimodal keys。冲突解决后也要重跑这张矩阵，因为 rebase 合并两边功能时最容易只保留默认路径。
  - 新增测试或新 payload 分支把旧代码从 dormant 变成 active 时，旧代码也进入本 PR 的 review surface。不能用 `git blame` 解释成“不是我写的”来降级；要沿调用链审被激活的旧行是否真能执行，尤其是之前只赋值不消费、现在开始索引/调用/切片的中间变量。
  - mock / fake runner 要匹配真实 abstraction，而不是只匹配裸 Python / PyTorch 对象。尤其审 property vs method（`.cpu` tensor 属性 vs `Tensor.cpu()` 方法）、CPU/GPU buffer wrapper、`.np` 镜像、`copy_to_gpu()` 生命周期；不确定时测试参数化覆盖 fake 形态和真实 wrapper 形态。
  - online serving e2e 的 edge case 不止模型 runner：审 request preprocessing 是否能通过，`chat_template` 从哪里来，tokenizer / processor / preprocessor artifacts 是否随真实 checkpoint 存在，`mm_processor_kwargs` 和 stage sampling params 是否按请求合成。transformers/vLLM 版本升级改变默认行为（如 transformers 4.44 禁默认 chat template）时，这就是当前 PR 的边界条件。
  - 新模型接入要审 shape-compatible semantic edge：`cos/sin` 顺序、activation、token order、scheduler step spacing、`pad_id == eos_id` attention mask、真实 tokenizer / processor 缺失是否早炸、stub smoke 是否被误当 real checkpoint 证据

不写 test 不要紧，但**必须在 commit message 或 review 自答里点名**这几个边界走了哪条分支。

### Audit #4：Surface area（这个 knob 真的必要吗？）

新增的 CLI arg / API 字段 / extra_args key / 配置项——**问**：

- help text 在解释什么不该解释的事（"defaults to X for case A, Y for case B"）→ 信号：默认值本来就是 caller 算好的，不该再让 user 指定（PR #3626 comment 1）
- 参数能从另一个参数派生 → 不该独立暴露（target_ratio_idx 能从 (h, w) 派生 → 直接传 (h, w)）
- 多个 enum knob 互斥但都暴露了 → 应该合并 / 用一个判别字段
- 内部方法新增 optional fast-path 参数也要当 surface area 审：docstring 是否写清 device / contiguous / shape / length / ownership / `None` fallback contract
- optional tensor/cache/staged/buffer 参数要拆两张 contract：
  - data contract：device、dtype、shape、contiguous、长度、detach/lifetime，由数据 owner 校验
  - execution-context contract：rank、stage、mode、stream、cache enabled 状态，由知道上下文的 caller owner 校验
- 新增 optional 参数不能靠“现在只有一个 caller”保证安全；wrong caller 必须在 owner 边界早炸，而不是 silent fallback 或晚点产出错 payload
- backend choice 是 correctness surface：FlashAttention / SDPA / custom kernel 如果有 homogeneous span、mask layout、dtype 或 precision 约束，PR 里要能解释何时用、何时 fallback；内部 fallback 也要有日志和测试锚点
- 改共享 state/schema 类型（`NamedTuple` / dataclass / `TypedDict` / msgspec Struct / request-response schema）= shared ABI change：
  - `rg "<TypeName>\\("` 查所有构造点，尤其 positional constructor
  - `rg "<state_name>|<field_name>"` 查所有解包点、传递点、跨 runner 复用点
  - 新字段优先末尾默认值或 keyword 构造；不要让旧 positional 调用 runtime 才炸
  - 只有某一路需要字段时，先考虑专用 state，别污染共享 state
  - `py_compile` / `ruff` 不足以验证 arity compatibility，必须执行至少一个构造点 smoke

**反模式**：加 knob 是 cheap，删 knob 是 breaking change。**默认不加**，等 user 真的提需求再加。

### Streaming / API protocol audit（新增 stream/SSE/WebSocket 必跑）

新增 `stream` 参数、SSE chunk、WebSocket message、OpenAI-compatible response schema 时，把它当 public protocol surface，不要当内部 helper：

- 协议类型先落 protocol 层（如 `protocol/*.py`），生成逻辑住 serving/helper 层，API 层只做接参和 response 包装；如果 endpoint 里临时 yield dict，默认当 layering finding。
- 动手前 grep 既有 endpoint 和 output processor，优先复用现成 streaming / delta / error 机制（例如 `RequestOutputKind.DELTA`）；手写 previous-text、manual delta、custom DONE/error 风格默认要解释为什么不能复用。
- public API 字段、OpenAI-compatible 参数、SSE chunk schema 必须同步 docs；没有 docs 页也要在 PR 里说明不补的原因。PR body 的 Test Plan/Result 要写 docs coverage。
- 先 grep 仓库已有 streaming endpoint，逐项对齐 `normal chunk / validation error / EngineDeadError / generic exception / client disconnect / DONE` 行为；尤其 engine-dead 不能被 generic `except Exception` 吞掉。
- structured error 不能降级成裸字符串异常；`ErrorResponse` / `HTTPException` 的 status、type、code 必须能一路进 error chunk。
- 字段名叫 `delta` 就必须可 append；测试要模拟客户端把所有 delta 拼起来，断言最终文本/音频/状态正确。若支持 replacement，协议要显式表达 `full_text` / `reset` / snapshot，不要继续叫 delta。
- `[DONE]` 是协议事件，不是 finally 里的装饰；确认 error 后、empty final output、client cancel、engine-dead 各分支是否应该发，以及发几次。
- 新 streaming 路径不要只测 `200 text/event-stream`；至少补一个 4xx preservation、一个 engine-dead/shutdown、一个客户端重建状态测试。

---

## How to apply

### 自审（push 前）

逐条对照 4 项写 review note，不要心算"应该没问题"。**reviewer 第一眼看到的，自己第一眼也得看到**。每跑一项在 commit message 或 PR description 显式标 "AUDITS: 1✓2✓3✓4✓"。

### Sub-agent review（spawn 时）

用上面 **"✅ Sub-agent prompt 模板"** 那段——逐字粘贴。不要省略 "AUDITS RUN: 1,2,3,4 — N findings" 那行尾签——它强制子 agent 自检确实跑了 4 项，缺项就要补跑。

### 并行 multi-framing union（更稳）

3 个 sub-agent 各跑一项（duplication / layering / edge+surface），结果 union。比单 agent 全跑更难漏：

```
Agent A prompt: 只跑上面模板的 Audit 1（Duplication）。返回 finding 或 "none found"，
                 不要做其他维度。
Agent B prompt: 只跑 Audit 2（Layering）。同上。
Agent C prompt: 跑 Audit 3 + 4（Edge cases + Surface area）。同上。
```

收回三份结果**自己 union**，不要再 spawn 一个"汇总 agent"——那会再过一层 framing 漏斗。

---

## 反模式

- "sub-agent 说 OK 我就 push 了" → 子 agent 只答你问的，没问的不会说
- "我先 grep 过了" 但只 grep 了一处（仓库 OR upstream，不是 AND）
- 把 audit 当 "可选 thoroughness"，赶时间就跳——reviewer 永远不会跳，跳的代价是 review iteration
- "我 commit message 写了 trade-off" 但**没写边界条件**——trade-off 是设计选择，边界是 bug 入口

---

## Where this came up

- PR #3626 fix/hunyuan-image3-image-size: reviewer Bounty-hunter 4 条评论同根因（duplication + layering），sub-agent code check 全程说 OK。
- 用户：「我之前让子 task code check 他说没问题」「这是严重问题，你要学习从 review 角度去看问题」（2026-05-15）
- PR #3734 prefix-cache CPU staging：code check 无 P0/P1，但抓到四个 reviewer 视角问题：新增 `hidden_states_cpu` 参数 docstring 没写 CPU/contiguous/length contract；generic `_get_merged_tensors` 参数名泄漏 hidden-state caller 语义；只审了 data contract，漏审 execution-context contract（只能 last PP rank 创建/消费，wrong caller 要早炸）；给共享 `ExecuteModelState` 加必填字段后只补 AR runner，漏了 GPU generation runner 的旧 positional constructor，说明 shared state ABI 变更必须 grep 所有构造/解包点。
- PR #3734 rebase 到 main 后二次 owner audit：冲突解决保留了默认 HunyuanImage3 full-prefix 路径，但漏了 `requires_full_prefix_cached_hidden_states=False` 的 tail-only 模型；prefix cache on 时 runner 没准备 scheduled-token CPU payload，`combined_hidden_states=None` 后会切 `None[start:end]`。说明 rebase/cherry-pick 后要审状态矩阵，而不是只看冲突文件能编译。
- PR #3734 CI fix：新增 tail-only 单测把主线旧 typo `query_start_loc_cpu = self.query_start_loc.cpu` 从 dormant 变成 active，Buildkite 在 `query_start_loc_cpu[idx]` 报 method not subscriptable。第一版改成 `.cpu()` 又让真实 runner 里的 `.cpu` tensor 属性报 `'Tensor' object is not callable`。说明“旧代码不是我写的”不能从本 PR 行为面移除；同时 mock 不能只用裸 `torch.Tensor` 形态，必须对照真实 runner wrapper 的 property/method contract。
- PR #3723 HunyuanImage3 IT2I image edit streaming：happy path tests + lint 过，但 review 抓到 EngineDeadError 被 generic SSE error 吞掉、ErrorResponse 400 被 ValueError 降级成 500、`ar_delta` replacement 不满足 append 语义。

---

## 链接

- spawn 子 agent 怎么写 prompt（避免偏见传染）：[review_delegation_framing](review_delegation_framing.md)
- duplication audit 的具体派生：[upstream_first_for_algorithm](upstream_first_for_algorithm.md)（in-repo equivalents 章节）
- 历史教训（Codex review 抓到的 API 设计模式）：[codex_review_lessons](codex_review_lessons.md)
