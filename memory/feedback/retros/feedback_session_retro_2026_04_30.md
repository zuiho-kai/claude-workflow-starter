---
name: 2026-04-30 HunyuanImage3 对齐会话复盘 — 9 条具体教训
description: 本次会话踩的所有坑的系统反思——baseline 测试方法、PR 分支管理、定量对比方法、API 参数验证。每条都有具体反例 + 应对规则
type: feedback
---

## 1. 测 HF baseline 前必先 grep 官方 demo（已单独落盘 feedback_check_official_demo_first.md）

**反例**：用 `model.generate(bot_task="auto", eos_token_id=[</recaption>])` 替代官方 `model.generate_image(bot_task="think_recaption")`。
**Why**：自定义 generate 函数（如 `generate_image`）内部传给 `model.generate()` 的关键参数（如 `stage_transitions`）是模型真实解码逻辑，不能省。
**How to apply**：grep README → 看官方 demo 用的是哪个 API → 照搬。烧的成本：30+ 分钟 + 用户一句"为什么不照着官方"。

## 2. 写 PR description 引用 commit hash 时，必须意识到 cherry-pick / rebase 会让 hash 失效

**反例**：cherry-pick 之前的 PR description 里用了旧 hash（`42ee44b6`、`88d16caa`...），cherry-pick 后 hash 变成（`d71981e7`、`27083f9c`...），用户打开 PR description 看到 hash 全对不上。
**Why**：cherry-pick / interactive rebase / amend 都改 hash。description 写完贴上去之后，任何 history 重写动作都会让"按 hash 引用"的条目过期。
**How to apply**：
- 写 PR description 引用 commit 时，**避免**只用裸 hash；用"hash + 一句话主题"的形式（如 `42ee44b6 Siglip2 list compat`），这样即使 hash 失效，主题还在能查
- 任何 history 重写（cherry-pick、rebase、amend、reset）后**必须** sed 一遍 description 把 hash 全替换
- 终极方案：写完 description 后跑一遍 `git log --oneline origin/main..HEAD | nl`，跟 description 里的 commit table 比对一致再贴

## 3. 开 PR 前必查 `git log origin/main..HEAD` 看看 commit 是不是全属于本 PR

**反例**：分支 `feature/hunyuan-t2t-sdpa-fa` 里夹着 5 个 GEBench CI commits（跟 AR alignment 完全无关），1 个 merge commit，导致 PR 总 diff = 96 files / 1287+1431 lines（实际真改动 = 4 files / 449+24 lines）。用户一句"分支好像受到我其他分支污染"我才查。
**Why**：merge / rebase 操作可能把上游 / 兄弟分支的 commit 拉进来。PR 开之前不主动盘点，reviewer 看到一堆无关改动会怀疑工作范围 + 审查疲劳 + 可能拒绝 merge。
**How to apply**：
- 开 PR 之前必跑 `git log --oneline origin/main..HEAD | nl`，逐条 commit 确认主题属于 PR
- 不属于的 commit → cherry-pick clean 分支重做（流程见 `hunyuan_image3_alignment_inventory.md` 顶部）
- diff stat 检查：`git diff --stat origin/main..HEAD` 改的文件应该跟 PR 主题强相关

## 4. 量化对比要按段分析，不要只看总长度

**反例**：fp32 MoE router 修完后总长度从 741→811 chars（**变长了 70**），我第一时间结论"看上去更远离 HF"。用户一句"刚刚我看总长度也有修复"才让我重新拆段——发现 think 段从 446→482（更接近 HF 的 466，差距从 -20 → +16），变长来自 recaption 段（修好之后 think 写得更准 → recaption 跟着展开更细）。
**Why**：复合输出（如 think + recaption）的总长度受多段联动影响，单看总长度会误解每段单独的进展。
**How to apply**：对比文本输出时按结构分段（用 regex 找 `</think>` / `<recaption>` / 段落分隔符），每段单独算长度 + 内容差异，再做总结。如果只能看总长，标明"含哪些段"避免误读。

## 5. CJK 文本必须明确 "chars" vs "bytes"

**反例**：`wc -c file.txt` 报 "1354 bytes"，lastwords 里写 "1354 chars"——其实是 bytes（CJK 一个字 ≈ 3 bytes，466 chars × ~3 ≈ 1354 bytes）。我前期混着用，导致初期对比表的"chars" 数字其实是 bytes。
**Why**：CJK 字符在 UTF-8 下是 3 bytes，`wc -c` / `len(bytes)` 跟 Python `len(str)` 差 ~3 倍。
**How to apply**：CJK 输出对比的脚本里必须用 `len(s)` (chars) **和** `len(s.encode())` (bytes) 都报，并明确标注。memory 里写历史数字时同样标 "chars" 还是 "bytes"。

## 6. HF `prepare_model_inputs` 返回的 dict 已含 generate 参数，覆盖前必先 pop

**反例**：`model.generate(**kw, max_new_tokens=2048, eos_token_id=[...])` 报 `TypeError: got multiple values for keyword argument`。kw 里 `max_new_tokens` / `eos_token_id` 是 generation_config 自动注入的。烧两次重跑（每次模型加载 1 分钟）。
**Why**：HF transformers 的 `prepare_model_inputs` (或类似的)会把 generation_config 里的所有参数 spread 进返回 dict，方便直接 `**kw` 调 generate。但用户想覆盖时撞 dup keyword。
**How to apply**：调 generate 前**总是**先 `kw.pop("max_new_tokens", None); kw.pop("eos_token_id", None)`（pop 任何要覆盖的 key），再传新值。这条对所有 HF 模型适用，不只是 HunyuanImage3。

## 7. lastwords / memory 里的具体 API 参数值，使用前必须本地 grep 验证

**反例**：lastwords 里写 `bot_task="think_recaption"`，我直接用，结果 HF tokenizer 报 `AssertionError: bot_task should be one of ['image', 'auto', 'think', 'recaption', 'img_ratio']`——`tokenizer.apply_chat_template` 不接受 `"think_recaption"`，但 `model.generate_image()` 接受（不同 API 层）。
**Why**：上一次会话写 lastwords 时可能在不同的代码路径下用过那个值，新会话直接套到不同 API 调用上会撞兼容性。
**How to apply**：使用 lastwords / memory 里的具体值（API 参数、token id、配置选项）前，**先 grep 一下源码**确认在你要调用的 API 里它是合法值。10 秒的验证省 30 分钟 debug。

## 8. 远端 SSH 断连时要等再试，避免短连接风暴

**反例**：HF baseline 长任务跑了 10+ 分钟，期间多次 SSH timeout，我立刻重试 → 又 timeout → 又重试，反复 5+ 次都失败。
**Why**：网络拥塞 / SSH server 限流 / 容器侧资源紧张时，短间隔重连会让恢复更慢。
**How to apply**：SSH timeout 后先 `sleep 60` 再试。如果连续 2 次失败，等 5 分钟。等待时可以本地干别的活（写 memory、改 PR description）。

## 9. rolling 写同一个文件时，旧版本 snapshot 可能已经丢失

**反例**：测试脚本固定写 `/tmp/step1_omni_out.txt`，第一次跑产出 811 chars 输出，第二次跑（加 stop fix）覆盖成 482 chars。后来想存"811 chars 中间状态"到本地——文件已经没了，只能在 README 里记录"811 chars 中间状态不在 disk"。
**Why**：固定输出路径方便测试脚本但不方便归档。
**How to apply**：归档/对比目的的测试脚本，输出文件名加时间戳或 mode 标识（如 `/tmp/step1_omni_out_${MODE}_${TIMESTAMP}.txt`）。或者每次重要 run 之后立刻 `cp` 到带后缀的归档名（如 `cp /tmp/step1_omni_out.txt /tmp/step1_fp32_no_stop.txt`）。

## 总结：本次会话单 session 烧的 GPU + 时间

| 失误 | 烧的成本 |
|---|---|
| 1. baseline 测试方式不照官方 | ~30 分钟 GPU + 多轮 explain |
| 6. max_new_tokens / eos_token_id 重复传 | 2 次模型加载 ≈ 2 分钟 |
| 7. bot_task="think_recaption" 直接用 | 1 次模型加载 + assertion 报错 ≈ 1 分钟 |
| 8. SSH 断连快速重试 | ~10 分钟 idle |
| 3. 分支污染拖到用户问才查 | 用户介入修分支管理 |

合计预估：~45 分钟 + 一次用户主动 escalation。如果按 9 条规则严格执行，可以省掉 30+ 分钟。

## 跟现有 feedback 文件的关系

- 第 1 条 → 详见独立 `feedback_check_official_demo_first.md`
- 第 4-5 条 → 补充到 `feedback_alignment_debug_pitfalls.md` 第 5、6 条
- 第 2-3 条 → 通用 git/PR 管理，新开 `.claude_errors/git_and_pr_branch_pollution.md`
- 第 6-7 条 → HF API 调用陷阱，单独条目
- 第 8 条 → 远端 SSH 操作经验，可加进 `ssh_connection_pattern.md`
- 第 9 条 → 测试归档习惯
