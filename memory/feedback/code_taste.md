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

坏味道：

- entrypoint 自己算模型内部 bucket id
- pipeline 复制 processor 里已有的 resize/crop 算法
- test 为了 import 方便放到无关 test module
- consumer hardcode producer 的 enum / token range / valid values

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
- image processor resize/crop → image processor / pipeline alignment test
- serving request 字段 → serving / protocol test
- example CLI 参数 → example 或 entrypoint smoke

坏味道：

- 一个测试类名和文件名主题完全不同
- import 某 helper 方便，所以塞进最近的 test 文件
- regression test 只测了 helper 本身，没测真实 caller path

**规则：reviewer 问“why need this test here?”，就是测试位置失败。先移动，不要解释。**

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

**规则：加参数很便宜，维护参数很贵。没有明确用户语义的 knob 不加；已有方法新增参数时，contract 不写进 docstring 就不算完成。**

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
