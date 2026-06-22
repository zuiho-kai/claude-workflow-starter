---
name: code_taste
description: 写代码前必读的人工 reviewer 代码品味规则：命名、归属、复用、测试位置、注释、API 面、diff 气味。用于防止“能跑但一眼会被人工 reviewer 打回”的改动。
type: feedback
---

# Code Taste：写代码前必读

**硬规则：凡是要写业务代码、测试代码、示例代码、API 字段、CLI 参数、helper 函数，动手前必须先读本文件。**

这不是“多跑一个 pass”。人工 reviewer 抓的是代码气味：名字误导、逻辑住错层、helper 重复、测试放错、注释没解释策略、API 面膨胀、diff 像临时补丁。测试通过只能证明“这条路径没坏”，不能证明代码有品味。

来源：PR #3626 后续 review。功能基本正确，但 Bounty-hunter 仍指出：

- `force_ratio` 命名让人分不清 force size 还是 force ratio token
- PackedRoutingCompat 测试放在 fused MoE 文件，行为归属不对
- pipeline 里复制 resize/crop helper，而不是放到 image processor 复用
- infer-align 后处理策略缺注释，人工 reviewer 不知道为什么这么分支

## 0. 写前先问：这代码会不会像临时补丁？

如果答案里出现以下任意一句，先停：

- “先放这里吧”
- “这个名字差不多”
- “测试放这里也能跑”
- “复制一份最省事”
- “reviewer 应该能看懂”
- “这个参数以后可能有用”

这些不是小瑕疵，是人工 reviewer 最容易抓的打回点。

## 1. 命名：名字必须说清机制，不要说感觉

变量 / 函数 / 参数名必须回答两个问题：

- 控制的对象是什么？
- 控制的机制是什么？
- 名字是否匹配它所在 helper 的抽象层级？

坏味道：

- `force_ratio`：不知道 force size、aspect ratio、bucket ratio，还是 token
- `align_size`：不知道 align input、output、bucket，还是 VAE shape
- `compat`：不知道兼容哪个版本、哪个签名、哪个路径

好名字：

- `force_ratio_token_from_user_size`
- `infer_align_image_size`
- `target_height` / `target_width`，下游自己 resolve bucket
- `accepts_legacy_four_arg_routing_call`

helper 层级命名：

- hidden-state 专用 helper 里可以叫 `hidden_states_cpu`
- generic tensor merge helper 里不要叫 `hidden_states_cpu`，用 `tensor_cpu` / `staged_cpu_tensor`
- runner 负责 staging 时可以叫 `hidden_states_cpu_staging`，cache owner 只消费 staged tensor contract

**规则：名字被 reviewer 问“what is X?”或“why is a generic helper using caller-specific wording?”，就是名字失败。不要靠注释补救误导性名字，先改名。**

## 2. 归属：逻辑必须住在数据 owner 那一层

判断逻辑归属，不看“哪个文件最方便改”，看“这段逻辑操作的数据长期归谁持有”。

- resolution / bucket / resize-crop：属于 image processor / resolution group
- AR token 限制：属于 AR sampler / model executor
- DiT VAE/VIT pre/post：属于 diffusion pipeline / image processor
- HTTP 字段透传：属于 serving / protocol，不能在这里 resolve 模型内部概念
- CLI 示例：只负责把用户输入转成 engine 参数，不拥有算法决策
- shared serving / chat 路径：只负责保留用户 payload 语义，不能把某个模型的 multimodal key 规则推广成全局规则；`image` / `img2img` / `images` 这类 key 的 owner 是具体 model parser / pipeline consumer

坏味道：

- entrypoint 自己算模型内部 bucket id
- pipeline 复制 processor 里已有的 resize/crop 算法
- test 为了 import 方便放到无关 test module
- consumer hardcode producer 的 enum / token range / valid values
- 为了修 HunyuanImage3 把 shared chat path 的 `multi_modal_data["img2img"]` 改成 `["image"]`，但没有 grep Bagel / Flux / GLM / Hunyuan 各自 parser

**规则：如果要把数据搬出去才能算，通常是逻辑放错层。把逻辑搬到数据 owner，而不是复制数据。**

## 3. 复用：新 helper 默认有罪，先 grep

新增 helper 前必须 grep：

- 同 repo 是否已有同概念函数 / class / 常量
- upstream / HF reference 是否已有同算法
- AR 版和 DiT 版是否已有一边实现过
- tests 是否已有 fixture / fake / helper 可复用

常见重复信号：

- 名字只差 `center` / `target` / `compat`
- 参数列表长得一样
- 注释里写“mirrors X”
- 测试里为了对比自己又写了一份 reference 实现

**规则：写出“mirrors X”时，下一步不是提交，是问为什么不直接复用 X。**

## 4. 测试位置：测试放行为 owner，不放方便 import 的地方

测试文件归属要让 reviewer 一眼知道为什么在这里：

- sampler 行为 → sampler test
- MoE kernel / fused op → fused MoE test
- AR routing / model-executor helper → HunyuanImage3 routing / model-executor test，不要塞进 fused MoE 或 sampler 这种“附近文件”
- image processor resize/crop → image processor / pipeline alignment test
- serving request 字段 → serving / protocol test
- example CLI 参数 → example 或 entrypoint smoke

坏味道：

- 一个测试类名和文件名主题完全不同
- import 某 helper 方便，所以塞进最近的 test 文件
- regression test 只测了 helper 本身，没测真实 caller path

**规则：reviewer 问“why need this test here?”，就是测试位置失败。先移动，不要解释。** 如果一个测试从 A 文件移到 B 文件后仍需要口头解释“其实它测的是另一个模块”，说明还没移到 owner；新建 dedicated owner test 文件比污染相邻 test 更好。

### 测试 scope：每个新增测试都要能绑定当前 diff

新增测试前必须写出它保护的行为来源：

- reviewer comment 指向的行为；
- 当前 PR 新增/修改的 public/internal contract；
- 当前 PR 修复的明确 bug；
- 防止刚才修复 diff 再次回退的最小 regression。

不满足这四类之一，就是测试膨胀。测试“看起来有价值”不够；如果它只是在保护一个 over-scope defensive patch，patch 删除时测试也必须删除。

**PR #3626 反例**：为 Bagel sanitizer patch 新增 `test_bagel_*`，但 Bagel 并不是当前 PR 的 root-cause owner；实际要保护的是 shared chat-completions path 继续输出 `multi_modal_data["img2img"]`。因此 Bagel sanitizer 测试必须随 patch 删除，保留 serving 层 img2img key regression test。另一个 no-size ratio stop-id 测试也不是 Bounty comment 或本次修复必需行为，删除后不影响当前 PR 的 reviewer-facing coverage。

**提交前测试清单**：`git diff --name-only origin/main..HEAD` 里每个 test 文件都要能用一句话回答“这个测试对应哪条代码行为变化”。答不出来就删，或把测试移到真正 behavior owner。

## 5. 注释：只解释策略和不变量，不解释语法

需要注释的地方：

- 和 upstream / HF 官方行为对齐的策略
- 多分支 fallback 的选择顺序
- 单图 / 多图 / no image / bucket mismatch 这种非显然策略
- 为什么传原始参数而不是派生值
- 为什么保留一个看起来多余的边界判断

不需要注释的地方：

- “set height”
- “resize image”
- “loop over items”
- “if value is None”

**规则：人工 reviewer 不需要你解释代码在做什么，他需要知道为什么这个策略是对的。**

## 6. API 面：新增 knob 默认不通过

新增 CLI arg / API field / config / extra_args key 前必须回答：

- 能不能从已有参数派生？
- 默认值是不是会和另一路默认值打架？
- 用户是否真的需要直接控制它？
- 下游是否已经有更原始、更稳定的表达？
- 加了以后怎么删？删不了就更要谨慎。

新增 request 参数、`extra_body` / `extra_args` key、`mm_processor_kwargs`、multimodal key、AR↔DiT bridge 字段时，先写 contract matrix，不写就不要动手：

- ingress：top-level、nested `extra_args`、CLI/example、legacy caller 是否都能表达同一语义？
- value shape：bool、string bool、`None`、0/1、sentinel、缺省分别怎么 normalize？
- owner：语义归 serving/protocol、bridge、pipeline、processor、还是 model config？
- consumer：下游实际读哪个 key；旧 key 是否兼容；unsupported path 是 fail fast 还是 no-op？
- consumer-specific default：同一个字段给不同 consumer 时默认值是否一致？如果 tokenizer / system prompt / scheduler / cache / backend 需要不同派生值，必须显式拆成不同局部变量，禁止用一个 normalized value 到处传。
- no-op：没有 condition image / feature disabled / empty image list 时，这个字段应该消失、保留到 downstream，还是 structured error？
- docs/tests：docs、bad-path test、string-bool test、legacy-key/multimodal-key test 在哪里？

优先传原始事实，而不是传过早派生的内部概念：

- 传 `(height, width)`，让 owner resolve ratio bucket
- 不传 `target_ratio_idx` 这种内部 token，除非用户真的在控制 token

新增函数参数 / optional fast path 也算 API 面，即使只是内部方法：

- docstring 必须同步新增参数，尤其是 optional fast path 的 contract
- 写清楚 ownership：谁创建、谁消费、是否允许 fallback
- 写清楚 tensor 不变量：device、contiguous、shape/layout、覆盖长度、dtype 是否必须一致
- 写清楚 execution-context 不变量：只能在哪个 rank / stage / mode / stream / cache enabled 状态下存在
- 写清楚 `None` 语义：是走旧路径、禁用路径，还是缺省自动推导
- data contract 放在数据 owner 校验；execution-context contract 放在知道上下文的 caller owner 校验
- wrong caller 必须早炸：新增 optional 参数不能靠“当前只有一个 caller”保证安全

改共享 state/schema 类型也算 API 面，即使它只是内部 `NamedTuple` / dataclass / `TypedDict` / msgspec Struct：

- 先 `rg "<TypeName>\\("` 查所有构造点，尤其 positional 构造
- 再 `rg "<state_name>|<field_name>"` 查所有解包点、传递点、跨 runner 复用点
- 新字段优先放末尾并给默认值，或把所有构造点改成 keyword；不要在中间插必填 positional 字段
- 如果只有某一路需要字段，先问是否该拆专用 state，而不是污染共享 state
- 至少跑一个能执行构造点的 smoke；`py_compile` / `ruff` 抓不到 `NamedTuple.__new__` arity runtime error

**规则：加参数很便宜，维护参数很贵。没有明确用户语义的 knob 不加；已有方法新增参数时，contract 不写进 docstring 就不算完成。**

**PR #3626 反例**：`infer_align_image_size` 不是单个 pipeline bool。它同时是 OpenAI-compatible request 字段、`extra_args` 字段、`mm_processor_kwargs`、DiT pipeline extra arg、processor 行为开关。只在 top-level 做 bool parse，漏 nested `extra_args`，会让 `"false"` 字符串变 true；只在 image-edit endpoint 写 `img2img` key，漏 DiT consumer 只读 `image` / `images`，会丢 condition image；T2I/generation 没有 condition image，却把 flag 塞进 prompt-side `mm_processor_kwargs`，会把纯文本请求切到 multimodal processor 路径。以后这类改动必须先按 contract matrix 审，不准靠“当前 caller 传的是 bool / 当前 endpoint 这么命名”写局部 patch。**

**PR #3626 rebase 反例**：修 HunyuanImage3 的 `image` key consumer 时，把 shared chat-completions img2img path 里的 `multi_modal_data["img2img"]` 改成 `["image"]`。这对 HunyuanImage3 / GLM 可能能过，但 Bagel 的 `OmniBagelDataParser` 明确注册 `img2img` parser，并用它产出 `pixel_values_img2img`。这类改动必须先列跨模型 consumer matrix：

| Key | 典型 consumer | shared path 能否直接改 |
| --- | --- | --- |
| `image` | HunyuanImage3 / GLM / 多数 image understanding 或 DiT bridge | 只能在对应 owner path 使用 |
| `img2img` | Bagel / Flux Kontext 等 img2img parser | 共享 chat path 必须保留，除非每个 consumer 都有兼容层 |
| `images` | 部分 diffusion pipeline batch / multi-image 输入 | 只能按 pipeline consumer 明确转换 |

**规则**：共享 serving / chat path 里改 multimodal key 前，必须 `rg '"img2img"|"image"|"images"' vllm_omni/model_executor vllm_omni/diffusion tests`，并说明每个受影响模型是保留、转换、还是不适用。不能把一个模型的正确 key 当成仓库全局正确 key。

### 分叉执行路径：禁止复制 request parsing，必须复用 owner helper

触发条件：
- 给现有功能新增 step-wise / graph / cache / batching / serving / offline / benchmark 等第二条执行路径。
- 新路径需要复用 normal path 的 request 字段、`extra_args`、prompt dict、multimodal payload、KV payload、system prompt、scheduler 参数或 backend 参数。

硬规则：
- normal path 和新路径不能各写一份 parsing / normalization / validation 逻辑。必须把字段解析放到数据 owner 的单一 helper，两个路径都调用它。
- helper 返回值要按 consumer 拆名，不要把“用户原始值”“模型/tokenizer 值”“system prompt 值”“cache/backend 值”混在一个变量里。
- 如果某个 consumer 需要特殊默认值，变量名必须体现 consumer，例如 `model_bot_task`、`system_prompt_bot_task`，不要叫泛泛的 `bot_task`。
- 新路径只允许在路径专属约束处和 normal path 分叉，例如 step path 不支持 image editing、graph path 不支持某类 cache；分叉处必须早炸或明确 no-op，不能静默跳过。
- 测试至少覆盖一个非默认字段和一个默认字段。只测默认值等于没测 request parsing parity。

Reviewer 自检问题：
- 这个字段从 ingress 到每个 consumer 是不是一条链路？
- 新路径是不是复制了 normal path 的 10 行 parsing？
- 同一个 normalized value 有没有被传给两个语义不同的 consumer？
- 默认值是用户语义默认，还是某个 consumer 的内部默认？

**一句话规则**：新增执行路径时，目标不是“新路径能跑”，而是“新路径和 normal path 共享同一套 request 语义；只在明确声明的不支持能力上分叉”。

## 7. Diff 气味：提交前看人工 reviewer 第一眼

提交 / push 前必须看 diff，不只是跑测试：

```bash
git diff --stat origin/main...
git diff origin/main... -- <changed-files>
```

看这些气味：

- 文件列表是否超出 PR 主题
- 新 helper 是否像复制品
- 变量名是否需要口头解释
- 测试文件名和测试类名是否一致
- 注释是否解释了策略来源
- public surface 是否膨胀
- 新增参数的 docstring / contract 是否同步
- 新增参数的执行上下文 guard 是否在正确 owner：rank/stage/mode 不对时是否立刻报错
- 共享 state/schema 字段变更是否 grep 过所有 constructor / unpack / consumer，positional arity 是否兼容
- generic helper 的命名是否被某个 caller 语义污染
- 是否出现“兼容一下”“兜底一下”的 silent fallback

**规则：如果 diff 需要你在 review comment 里解释“其实这是因为…”，优先把代码/命名/注释改到不需要解释。**

## 8. 人工 reviewer 模拟问题

每个新增逻辑块必须能直接回答：

- 为什么放这里？
- 为什么叫这个名字？
- 为什么不复用已有实现？
- 为什么需要这个测试，为什么在这个文件？
- 这个默认值为什么对？
- 这个 edge case 谁处理？
- upstream / official 行为对应哪段？
- 以后加第二个模型 / 第二个 backend 会不会复制第三份？
- 新增 optional 参数被未来 caller 误传时，会在哪里失败？是早炸还是静默 fallback？
- 这是不是 shared state ABI change？所有构造点、解包点、复用者都查过了吗？

答不出来，先别写或先改设计。

## 9. Review 评论：锚点不是装饰

处理人工 inline review 时，代码品味的第一步是尊重锚点。reviewer 把评论挂在哪几行，那几行就是问题主体；评论里的 `it` / `this` / `here` / `strategy` 默认指锚点里的最近代码实体。

坏味道：

- 评论锚在 output alignment，却去改 condition-image crop helper
- 评论说 “add it to image processor”，但没有先确认 `it` 指锚点里的哪段策略
- 改了相邻概念后就认为“这条评论已处理”
- 只加注释，但锚点里的逻辑仍住在 reviewer 质疑的 owner

**规则：每条 inline review 动手前先写 action mapping：Comment / Anchor / Pronoun target / Reviewer asks / Code action / Done check。详见 [reviewer_lens_audit](reviewer_lens_audit.md) 的 Inline review 处理规则。**

## 10. 和 reviewer_lens_audit 的关系

`reviewer_lens_audit.md` 是 push 前 / sub-agent review 用的 audit 模板。

本文件更早触发：**写代码前读**。它的目标是让第一版代码就少一点“AI 补丁味”，不要等 reviewer 或 sub-agent 才发现。

## 11. 触发词

用户说以下话，下一次写代码前必须更认真读本文件：

- “代码品味”
- “人工 reviewer”
- “为什么会被发现那么多问题”
- “以后写代码必须看”
- “不要只是能跑”
- “像补丁”
