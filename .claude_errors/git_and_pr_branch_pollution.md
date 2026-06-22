# Error Book: Git / PR 分支管理

## 2026-04-30 — feature/hunyuan-t2t-sdpa-fa 分支污染 + cherry-pick 后 hash 失效

**症状**：
- 分支 `feature/hunyuan-t2t-sdpa-fa` 上 PR #3243 显示 96 files / 1287+1431 lines diff
- 实际真改动只有 4 个 hunyuan_image3 文件 / 449+24 lines
- 用户开始 review 时一句"分支好像受到我其他分支污染"才发现问题

**根因**：
分支夹带了 6 个不属于本 PR 的 commit：
- `3e392b2` [CI] add GEBench T2I accuracy test to nightly pipeline
- `caa159c` [CI] use full_model run-level
- `497a01f` [CI] add --gebench-t2i-only flag
- `b01f469` [CI] fix summarize fallback for t2i-only mode
- `44871a0` Address HunyuanImage GEBench review comments
- `2719abca` Merge remote-tracking branch 'origin/main' into feature/hunyuan-t2t-sdpa-fa

这些来自 `feat/hunyuan-image3-accuracy-ci` 分支（GEBench CI 工作），通过 merge 拉进来时连带一起进了本 PR 范围。**多分支并行工作时**这种污染常发生：从 origin/main rebase / merge 时，如果其他分支已经 merge 进 main，那些 commit 又会跟新写的 commit 一起 push 到本 PR 分支。

**解法**：
```bash
# 从 origin/main 起新分支，只 cherry-pick 真正属于 PR 的 10 个 commit
git checkout -b feature/hunyuan-image3-ar-alignment origin/main
for h in 42ee44b6 80617a1d 88d16caa 80e0237f 42c2f349 0a63ab5e a7a5ab3f 80cbaa3f 0413c2c2 40ac16cc; do
    git cherry-pick "$h" || break
done
# 验证 diff stat 干净
git diff --stat origin/main..HEAD   # 应该只动 4 个 PR 范围内的文件
# Force-push 到 PR 分支
git push fork feature/hunyuan-image3-ar-alignment:feature/hunyuan-t2t-sdpa-fa --force-with-lease
git push zuiho-kai feature/hunyuan-image3-ar-alignment:feature/hunyuan-t2t-sdpa-fa --force-with-lease
```

cherry-pick 后所有 commit hash 变了：

| 旧 hash | 新 hash | 主题 |
|---|---|---|
| `42ee44b6` | `d71981e7` | Siglip2 list compat |
| `80617a1d` | `d360569a` | T2T instruct format |
| `88d16caa` | `27083f9c` | Unify chat template |
| `80e0237f` | `ea809348` | Assistant: prefix |
| `42c2f349` | `7bd429ed` | build_prompt_tokens |
| `0a63ab5e` | `3d415e17` | docs: timestep |
| `a7a5ab3f` | `8a1a4af9` | docs: image preprocessing |
| `80cbaa3f` | `41d29432` | VAE pixel cast |
| `0413c2c2` | `31c2fa56` | fp32 MoE router |
| `40ac16cc` | `07d8cf0d` | stop at </think> |

**对未来的提醒**：
1. **开 PR 前必查**：`git log --oneline origin/main..HEAD | nl` —— 逐条 commit 主题确认全属于本 PR
2. **diff stat 检查**：`git diff --stat origin/main..HEAD` —— 改的文件应该跟 PR 主题强相关，无关文件超过 1-2 个就要查
3. **避免 merge from origin/main**：要同步上游用 rebase 不用 merge（merge commit 会把上游所有合并的 PR 都"拉进"本分支的 log）
4. **cherry-pick 后必更新 PR description 里的 hash 引用**——old hash 在新分支上不存在，链接会失效
5. **多 worktree 工作时分清 base**：每个 worktree 起 branch 时明确 `git checkout -b xxx origin/main`，不要从当前 HEAD 起新分支

---

## 同期教训：PR description 里 hash 引用 cherry-pick 后失效

**症状**：cherry-pick 之前我的 PR description 里 commit table 用了旧 hash（`42ee44b6`...），cherry-pick 后 hash 变成（`d71981e7`...），用户打开 PR description 看到 hash 全对不上 GitHub 上的实际 commit。

**对未来的提醒**：
- 写 PR description 引用 commit 时**避免**只用裸 hash；用 `<hash> + 一句话主题`，hash 失效时主题还能查
- cherry-pick / rebase / amend 后**必须**重新跑一遍 `git log --oneline origin/main..HEAD` 跟 description 比对
- 终极方案：写完 description 跑 sed 一遍把 hash 替换成最新值，再贴

---

## 同期教训：多分支并行工作时 worktree 状态确认

本次本地有 N 个 worktree（看 `git branch -a` 一堆 `bounty-hunter/*`、`feat/*`），任何一个 worktree 误操作都可能影响 PR 分支。

**规则**：
- 每个 worktree 进去后第一件事：`git status -s` + `git branch --show-current` + `git log --oneline -3` 三连，确认在对的分支 + 干净状态
- 长会话中跨 worktree 切换时同样三连
- worktree 名字遵循 `wt-<purpose>` 约定（CLAUDE.md 22 条规则之一）便于识别

---

## 2026-05-20 — 违反 worktree 规则，在主仓工作区直接 apply_patch

**症状**：用户要求实现 HunyuanImage3 DiT step-wise grouped batching。我已读 `CLAUDE.md`，但直接在 `D:\vllm-omni\vllm-omni` 执行 `apply_patch`，导致主仓工作区出现业务改动：

```text
 M vllm_omni/diffusion/models/hunyuan_image3/pipeline_hunyuan_image3.py
 M vllm_omni/diffusion/sched/base_scheduler.py
 M vllm_omni/diffusion/sched/interface.py
 M vllm_omni/diffusion/worker/input_batch.py
```

当时 git root 是 `D:/vllm-omni/vllm-omni`，分支是 `codex/pr-3626-review-fixes`，不是 `D:\vllm-omni\wt-*` worktree。

**根因**：
- 把“代码仓库在 `D:\vllm-omni\vllm-omni`”误执行成“可以在这里写代码”。
- 开工前只看了 `git status`，没有把 D2/D4 转成写文件前的硬 gate。
- 在读代码阶段 cwd 留在主仓；进入编辑阶段没有重新确认 git root 是否是 `wt-*`。

**正确补救**：
1. 立刻停手，不继续在主仓完成实现。
2. 记录当前 `git status --short` 和 touched files。
3. 新建独立 worktree：
   ```powershell
   $repo = "D:\vllm-omni\vllm-omni"
   $wt = "D:\vllm-omni\wt-hunyuanimage3-step-batch"
   git -C $repo worktree add -b codex/hunyuanimage3-step-batch $wt origin/main
   ```
4. 把主仓里属于本次事故的 diff 迁移到 worktree 后，只撤回主仓中自己刚造成的这些文件改动。
5. 之后所有实现、测试、commit 都只在 `wt-hunyuanimage3-step-batch` 内进行。

**怎么避免**：
1. vllm-omni 业务代码任务里，`apply_patch` 前必须跑：
   ```powershell
   $root = git rev-parse --show-toplevel
   Split-Path $root -Leaf
   git status --short --branch
   ```
2. `Split-Path $root -Leaf` 不是 `wt-*` 就禁止写文件；先 `git worktree add`。
3. 读代码可以在主仓；从“读”切到“改”的瞬间必须重新执行 guard。
4. 如果用户贴了 `<cwd>D:\vllm-omni\workflow-starter</cwd>` 或当前 shell 位于主仓/非 worktree，不能凭上下文假设目标 worktree 已存在，必须显式创建或切换。

---

## 2026-05-19 — PR 描述没按 vLLM-Omni 模板写

**症状**：用户要求“给我 PR 描述”，我先给了自由格式 `Summary / Changes / Tests`，用户指出“要符合 vllmomni 格式”。仓库实际有 `.github/PULL_REQUEST_TEMPLATE.md`，固定为 `Purpose / Test Plan / Test Result`。

**根因**：没有先读 PR template，把通用 GitHub PR 格式套到了 vLLM-Omni。PR 描述是仓库公共接口的一部分，格式必须以仓库模板为准。

**解法**：写 PR 描述前先读：
```bash
cat .github/PULL_REQUEST_TEMPLATE.md
```
输出只保留模板要求的主体：
```markdown
## Purpose

## Test Plan

## Test Result
```

**怎么避免**：
1. 任何“给我 PR 描述 / 开 PR / yeet”请求，先读 `.github/PULL_REQUEST_TEMPLATE.md`，没有模板才用通用格式。
2. vLLM-Omni PR 描述必须用 `Purpose / Test Plan / Test Result`，不要用 `Summary / Changes / Tests`。
3. Test Result 里贴具体命令和结果；远端验证要写节点/目录/venv，但不要写无关流水账。

## 2026-05-20 — PR #3766 描述渲染失败、图片裂、Test Plan 不可复现

**症状**：
- PR 描述里图片使用 `tmpfiles` 临时外链，GitHub 页面裂图。
- Test Plan 写成 UT / regression 覆盖清单，用户实际要的是 e2e 怎么复现：跑什么脚本、临时 YAML 怎么写、怎么发请求、指标怎么比。
- PowerShell 写 PR body 时使用双引号 here-string，Markdown 三反引号被当成 escape，GitHub 上出现 `` `b + ash ``、tab + `ext` 一类乱码，代码块无法渲染。
- 用户评价“pr描述的markdown格式不对，一坨屎”。

**根因**：
- 把 PR body 当成“提交成功即可”，没有当成 reviewer-facing artifact 做渲染级验收。
- 没按需求聚焦 e2e 复现路径，拿内部验证清单替代用户要的脚本/YAML/请求。
- 图片外链选择没有稳定性标准。
- 没有读回检查 code fence、控制字符、图片 HTTP header。

**正确补救**：
1. 用 no-BOM UTF-8 文件重写 PR body；PowerShell 用单引号 here-string。
2. PR body 结构收敛为：
   ```markdown
   ## Purpose
   ## Test Plan
   ### Environment
   ### Run Command
   ### Temporary YAML
   ### Request Construction
   ### Metric Comparison
   ## Test Result
   ### E2E Evidence
   ### Run Metadata
   ### Accuracy Metrics
   ### Artifacts
   ```
3. 图片改用单独 artifact branch 上的 GitHub raw URL，并先 `HEAD` 验证 `200 image/png`。
4. `gh pr view --json body` 读回检查：
   - 包含真正的 ```bash / ```yaml / ```python code fence。
   - 不含 ASCII control chars。
   - Test Plan 能按机器、命令、YAML、请求、reference metric 复现。

**怎么避免**：
1. 更新 PR 描述后必须跑“PR body render gate”：
   ```powershell
   $view = gh pr view <PR> --repo vllm-project/vllm-omni --json body | ConvertFrom-Json
   $view.body.Contains('```bash')
   $view.body.Contains('```yaml')
   $view.body.Contains('```python')
   $view.body -match "[\x00-\x08\x0B\x0C\x0E-\x1F]"  # 必须 False
   ```
2. 图片 gate：
   ```powershell
   Invoke-WebRequest -Uri $url -Method Head -UseBasicParsing
   ```
   必须 `200` 且 `Content-Type` 是图片。
3. 用户要求 e2e / 精度 / 性能时，Test Plan 只写可复现 e2e。UT 覆盖最多一句带过，不要喧宾夺主。
4. PR 描述写完要从 reviewer 视角读一遍：不看聊天上下文，也能知道在哪里跑、用什么配置、发什么请求、怎么验证结果。

## 2026-05-19 — 业务代码写完后漏主动 sub-agent review

**症状**：HunyuanImage3 IT2I AR streaming 功能写完、测试过、PR 描述也写好后，用户手动提醒“开个 sub agent 去做 code check”。sub-agent 立刻发现 P1/P2：流式可能没有最终 image 仍 `[DONE]`、单阶段 `stream=true` 拒绝太晚、non-prefix AR delta 会污染 previous 文本。说明我 push 前自审不够，用户不提醒就会把问题带到人工 review。

**根因**：把 sub-agent review 当成用户可选动作，而不是 PR 交付硬卡点；而且如果 prompt 只是“code check”，容易护不住。正确姿势是按 `reviewer_lens_audit.md` 的四项（duplication / layering / edge cases / surface area）明确要求 findings 或 none found，再结合 `code_taste.md` 看命名、归属、复用、测试位置和 diff 气味。

**解法**：业务代码/测试代码写完、准备 commit/push/开 PR 前，主动 spawn sub-agent 做 reviewer-lens audit。sub-agent 返回后先处理 P0/P1/P2 或明确记录为什么不处理，再提交/推送。本次处理后补了 final-image error、early single-stage rejection、replacement delta 测试，并抽 `_prepare_diffusion_image_request()` 复用非流式/流式构造逻辑。

**怎么避免**：
1. 提交前 checklist 固定顺序：本地 diff 自审 → sub-agent reviewer-lens audit → 修 findings → ruff/pytest/必要远端验证 → commit/push。
2. sub-agent prompt 禁用“code check 一下 / 看有没有问题”这种开放但无审计框架的说法；必须列四项 audit，并要求每项 findings 或 none found。
3. 用户说“需求写完”不等于“可以直接 push”；只要涉及业务代码或测试代码，sub-agent review 是硬卡点。

## 2026-05-19 — 新 public API 字段 stream 缺文档被 reviewer block

**症状**：PR #3723 新增 `/v1/images/edits` 的 `stream` 表单参数和 SSE chunk schema，reviewer `hsliuustc0106` requested changes：`stream` 是新的 public API field，必须补文档说明 streaming response format、`ar_delta`、final image、`[DONE]` 以及何时使用。

**根因**：我把“代码 + 测试 + PR 描述”当成交付闭环，漏了 public API 的 docs surface。`code_taste.md` 已经写了 API 面规则，但我当时只用它看代码形状（helper 复用、edge cases），没有把“新增 API field 必须同步 docs”列成硬卡点；sub-agent review prompt 也没有要求检查 documentation surface，所以它抓到了行为问题但没抓 docs 缺口。

**解法**：补 `docs/serving/image_edit_api.md`：参数表新增 `stream`，新增 streaming response format 小节，写清只支持多阶段 HunyuanImage3 IT2I AR+DiT、SSE 顺序 `ar_delta` → `image` → `[DONE]`、error chunk 格式和 curl 示例；同时修该页原有未闭合 code fence/表格行，避免新增文档渲染失败。PR body 的 Test Plan/Result 同步写入 docs check。

**怎么避免**：
1. 任何新增 public API 字段 / CLI 参数 / config key / SSE chunk schema / OpenAI-compatible 参数，提交前必须 `rg` 对应 docs，并同步文档；没有文档页也要在 PR 里明确说明为什么不需要。
2. reviewer-lens 的 Surface area audit 要包括 docs surface：新增 knob 是否有用户语义、默认值、适用条件、响应格式和错误格式文档。
3. PR 描述的 Test Plan 不能只列代码测试；public API 变更必须列 documentation coverage，Test Result 至少有 `git diff --check` 或 mkdocs/markdown 渲染检查。

## 2026-05-19 — PR #3734 code check 抓到参数 contract 和 helper 命名品味问题

**症状**：PR #3734 prefix-cache CPU staging dedup 经过 code check 后没有 P0/P1 正确性问题，但有两个 P2 品味问题：(1) `update_omni_tensor_prefix_cache(..., hidden_states_cpu=...)` 新增 optional 参数后，Args docstring 没写 CPU / contiguous / 覆盖 token 长度 / layout contract；(2) generic `_get_merged_tensors` helper 的参数名叫 `hidden_states_cpu`，泄漏了 hidden-state caller 语义。

**根因**：实现时把注意力放在 hot path 行为和兼容 fallback 上，没把“新增内部参数”当 API surface 审；命名从 profiling 语境出发，没有回到 helper 所在抽象层级检查。

**解法**：把两条规则补进 `code_taste.md` / `reviewer_lens_audit.md` / `CLAUDE.md` F10：新增参数必须同步 docstring contract；generic helper 命名不能泄漏 caller-specific 语义。

**怎么避免**：
1. 任意方法新增参数（包括 internal optional fast path）都要补 docstring contract：ownership、device、contiguous、shape/layout、覆盖长度、`None` fallback。
2. helper 命名前先问“这个 helper 是 generic 还是 caller-specific”：generic helper 用 `tensor_cpu` / `staged_cpu_tensor` 这类抽象层级名字，专用 helper 才用 `hidden_states_cpu`。
3. push 前 diff 自审加两项：新增参数 docstring 是否同步；helper 名字是否需要在 PR comment 里额外解释。如果需要解释，优先改代码表达。

## 2026-05-27 — PR #3734 rebase 后漏掉 tail-only prefix-cache 状态矩阵

**症状**：把 PR #3734 rebase 到最新 main 并解决 `prefix_cache.py` / `gpu_ar_model_runner.py` 冲突后，两个 owner-framed sub-agent 都抓到同一个问题：`prefix cache enabled + requires_full_prefix_cached_hidden_states=False` 时，runner 不做 full-prefix hidden merge，但 downstream/pooler 仍需要本 step scheduled-token hidden payload。冲突解决后的代码只在 `self.omni_prefix_cache is None` 时准备 `hidden_states_cpu`，导致 `combined_hidden_states=None` 后 `_resolve_req_hidden_states()` 会切 `None[start:end]`。模块 owner 定 P0，项目 owner 定 P1。

**根因**：冲突解决只把 main 的 deferred mm cache 逻辑和 PR 的 hidden-state CPU staging fast path 合并到默认路径，没重新列状态矩阵。HunyuanImage3 profiling 覆盖的是 full-prefix hidden path；Qwen3-TTS 这类 `requires_full_prefix_cached_hidden_states=False` tail-only 模型没有进测试矩阵。ruff / py_compile / diff clean 都只能证明语法和格式，不能证明 feature-flag 组合语义。

**解法**：在 GPU runner 里增加 `needs_scheduled_hidden_payload` 分支：prefix cache 开启但模型 opt-out full-prefix merge 时，仍复用 execute_model 阶段的 `staged_hidden_states_cpu` 给 pooler payload 切分；如果缺 staged tensor 就早炸。同时补 `hidden_states_cpu` dtype fail-fast、merge-path contract docstring、tail-only prefix-cache 回归测试。

**怎么避免**：
1. 改 runner / prefix cache / pooler payload / shared execution state 后，rebase/cherry-pick 冲突解决必须重审状态矩阵：cache on/off、prefix hit/miss、feature flag true/false（如 `requires_full_prefix_cached_hidden_states`）、downstream req all/subset、last/non-last PP rank、staged CPU tensor None/fallback、deferred mm keys。
2. owner audit prompt 不能只问“看有没有问题”；project owner 查 repo integration/state ownership，module owner 查具体 contract/edge cases。两个结果里任一 P0/P1 必须先修再 push。
3. 性能 PR 的验证不能只覆盖 profiling workload 的默认模型路径；如果改动跨 runner/cache/payload owner，至少给非默认 feature flag 加一个 owner-boundary unit/smoke，或在 PR 里明确该分支不适用。

## 2026-05-27 — 双 owner sub-agent 放到事后，导致方案阶段漏问题

**症状**：PR #3734 rebase 后确实拉了两个 sub-agent，但时间点是在冲突解决和本地验证之后、准备 push 之前。sub-agent 抓到 P0/P1 后还要返工改方案、补测试、amend commit。用户指出核心问题是“想怎么修改的时候就必须提前拉两个 sub agent 去以项目 owner 和模块 owner 角度思考怎么改，每次事后有点笨”。

**根因**：把 sub-agent 当成 pre-push audit，而不是 design-time gate。等 patch 写完再问“有没有问题”，只能抓已经写出来的缺陷；真正该早发现的是 owner 边界、状态矩阵、测试矩阵和最小方案形状。

**解法**：把双 owner review 前移到“形成修改方案 / 写代码前”：module owner 先审模块 contract、state matrix、edge cases、测试；omni project owner 先审 repo ownership、API surface、PR evidence、跨 pipeline/backends 影响。事后 reviewer-lens 仍保留，但不能替代动手前的方案审核。

**怎么避免**：
1. 非平凡业务改动开始想方案时就开两个 sub-agent，prompt 明确要求“propose/review intended change before implementation”，不要传一个已写 patch 让它事后找 bug。
2. 两个 owner 任一返回 P0/P1，必须先改计划，再动手写代码；不能把“后面 push 前再修”当流程。
3. 可跳过范围只限纯 typo、格式、无行为文档改动；runner / prefix cache / shared state / pipeline / public API / 新模型 / batching / streaming 默认不能跳。

## 2026-05-29 — PR #3626 图片证据复用旧 head，且公开评论泄露内部 artifact path

**症状**：
- Reviewer 要求补贴 online accuracy 的 output image。
- 我从远端旧 artifact 拉取 `image_online.png`，验证它是 `PNG 1280x720` 后直接上传并贴到 PR。
- 评论里还写了：
  ```text
  Artifact source: /data/wzr/wt-pr3626-accuracy/tests/e2e/accuracy/artifacts/HunyuanImage-3_0-Instruct-online/image_online.png
  ```
- 用户指出这行不该出现；随后又要求 rebase 最新主干后重跑。

**根因**：
- 判断标准错了：把任务当成“补一张图片”，而不是“给当前 PR 状态补一组 reviewer-facing 证据”。
- 只验证 artifact 本身存在、能打开，没有验证它和当前 PR head / base / metrics 是同一轮。
- 当时旧 run 绑定的是 `9e2181430...`，而 PR head 已经发生变化；这种 mismatch 应该是 hard stop。
- 把内部执行追踪路径当成透明度信息写进公开 comment。远端 `/data/...` 路径对 reviewer 没复现价值，只会污染 PR 页面并暴露环境细节。

**正确补救**：
1. 立刻编辑评论，删除内部 artifact path，只保留图片。
2. 按用户要求 rebase PR branch 到最新 `origin/main`，force-with-lease 推回 Taffy PR branch。
3. 远端 worktree 同步到新的 PR head 后重跑 online accuracy。
4. 用新 run 生成的新图片、新 metrics、新 head 重新发干净 PR comment。
5. 清理本次 run 遗留进程，确认 4/5/6/7 释放。

**怎么避免**：
1. PR comment/body 贴测试图或指标前先跑 evidence provenance gate：
   ```powershell
   gh pr view <PR> --repo vllm-project/vllm-omni --json headRefOid,headRefName,headRepositoryOwner
   ```
   ```bash
   cat <status-file>
   grep -E 'HEAD=|WT=|EXIT_STATUS|1 passed|\\[ONLINE\\]' <log-file>
   stat <output-image>
   ```
   `headRefOid`、run `WT/HEAD`、图片 mtime/size 必须属于同一轮。
2. `headRefOid != run HEAD` 时，不能贴旧 artifact。用户说 latest / rebase 后 / current PR 时，先 rebase/sync/rerun。
3. 公开 PR comment/body 禁止写内部远端路径、`/tmp`、本地 `%TEMP%`、status/log 文件路径，除非用户明确要求 debug 细节。默认只写 reviewer 需要的信息：head、case、result、metrics、stable image URL。
4. 图片上传后先 `HEAD` raw URL 验证 `200 image/png`，并打开图片确认不是旧图/裂图/空图。
5. 发评论前本地读一遍 Markdown body，专门搜索内部路径模式：
   ```powershell
   Select-String -Path <body-file> -Pattern '/data/|/tmp/|AppData|Artifact source|status.txt|\\.log'
   ```
   命中就删，除非它是用户明确要求的调试记录。

**验收标准**：PR 页面上的图片和 metrics 可追溯到当前 head；评论没有内部路径；如果要引用历史结果，标题必须显式写历史 head，避免 reviewer 误解成 current-head evidence。
