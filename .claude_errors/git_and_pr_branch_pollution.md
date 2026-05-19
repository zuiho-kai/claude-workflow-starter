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
git push <GH_ORG> feature/hunyuan-image3-ar-alignment:feature/hunyuan-t2t-sdpa-fa --force-with-lease
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
