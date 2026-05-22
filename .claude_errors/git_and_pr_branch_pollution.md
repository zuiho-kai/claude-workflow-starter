# Error Book: Git / PR 分支管理

## 2026-04-30 — PR 分支污染：多分支并行工作时 merge 带入不属于本 PR 的 commit

**症状**：PR 显示 ~100 files 的大 diff，实际真改动只有 4 个文件。用户开始 review 时才发现分支被污染。

**根因**：分支夹带了若干不属于本 PR 的 CI 相关 commit，来自另一条并行功能分支，通过 merge 拉进来时连带一起进了本 PR 范围。**多分支并行工作时**这种污染常发生：从 origin/main rebase / merge 时，如果其他分支已经 merge 进 main，那些 commit 又会跟新写的 commit 一起 push 到本 PR 分支。

**解法**：
```bash
# 从 origin/main 起新分支，只 cherry-pick 真正属于 PR 的 commit
git checkout -b feature/<new-clean-branch> origin/main
for h in <sha1> <sha2> ...; do
    git cherry-pick "$h" || break
done
# 验证 diff stat 干净
git diff --stat origin/main..HEAD   # 应该只动 PR 范围内的文件
# Force-push 到 PR 分支
git push origin feature/<new-clean-branch>:feature/<old-branch> --force-with-lease
```

cherry-pick 后所有 commit hash 变了，记得更新 PR description 里的 hash 引用。

**对未来的提醒**：
1. **开 PR 前必查**：`git log --oneline origin/main..HEAD | nl` —— 逐条 commit 主题确认全属于本 PR
2. **diff stat 检查**：`git diff --stat origin/main..HEAD` —— 改的文件应跟 PR 主题强相关，无关文件超过 1-2 个就要查
3. **避免 merge from origin/main**：要同步上游用 rebase 不用 merge（merge commit 会把上游所有合并的 PR 都"拉进"本分支的 log）
4. **cherry-pick 后必更新 PR description 里的 hash 引用**——old hash 在新分支上不存在，链接会失效
5. **多 worktree 工作时分清 base**：每个 worktree 起 branch 时明确 `git checkout -b xxx origin/main`，不要从当前 HEAD 起新分支

---

## 同期教训：PR description 里 hash 引用 cherry-pick 后失效

**对未来的提醒**：
- 写 PR description 引用 commit 时**避免**只用裸 hash；用 `<hash> + 一句话主题`，hash 失效时主题还能查
- cherry-pick / rebase / amend 后**必须**重新跑一遍 `git log --oneline origin/main..HEAD` 跟 description 比对

---

## 同期教训：多分支并行工作时 worktree 状态确认

**规则**：
- 每个 worktree 进去后第一件事：`git status -s` + `git branch --show-current` + `git log --oneline -3` 三连，确认在对的分支 + 干净状态
- 长会话中跨 worktree 切换时同样三连
- worktree 名字遵循 `wt-<purpose>` 约定便于识别

---

## 2026-05-19 — PR 描述没按仓库模板写

**症状**：用户要求"给我 PR 描述"，先给了自由格式，用户指出要符合项目格式。仓库实际有 `.github/PULL_REQUEST_TEMPLATE.md`。

**根因**：没有先读 PR template，把通用 GitHub PR 格式套到了项目。PR 描述是仓库公共接口的一部分，格式必须以仓库模板为准。

**解法**：写 PR 描述前先读：
```bash
cat .github/PULL_REQUEST_TEMPLATE.md
```

**怎么避免**：
1. 任何"给我 PR 描述 / 开 PR"请求，先读 `.github/PULL_REQUEST_TEMPLATE.md`，没有模板才用通用格式。
2. Test Result 里贴具体命令和结果；远端验证要写目录/venv，但不要写无关流水账。

---

## 2026-05-19 — 业务代码写完后漏主动 sub-agent review

**症状**：功能写完、测试过、PR 描述也写好后，用户手动提醒"开个 sub agent 去做 code check"。sub-agent 立刻发现协议坏路径问题。说明 push 前自审不够，用户不提醒就会把问题带到人工 review。

**根因**：把 sub-agent review 当成用户可选动作，而不是 PR 交付硬卡点；而且如果 prompt 只是"code check"，容易护不住。正确姿势是按 `reviewer_lens_audit.md` 的四项（duplication / layering / edge cases / surface area）明确要求 findings 或 none found。

**解法**：业务代码/测试代码写完、准备 commit/push/开 PR 前，主动 spawn sub-agent 做 reviewer-lens audit。sub-agent 返回后先处理 P0/P1/P2 或明确记录为什么不处理，再提交/推送。

**怎么避免**：
1. 提交前 checklist 固定顺序：本地 diff 自审 → sub-agent reviewer-lens audit → 修 findings → ruff/pytest/必要远端验证 → commit/push。
2. sub-agent prompt 禁用"code check 一下 / 看有没有问题"这种开放但无审计框架的说法；必须列四项 audit，并要求每项 findings 或 none found。

---

## 2026-05-19 — 新 public API 字段缺文档被 reviewer block

**症状**：新增 streaming 参数和 SSE chunk schema，reviewer 指出这是新的 public API field，必须补文档说明 response format、各 chunk 类型、`[DONE]` 和何时使用。

**根因**：把"代码 + 测试 + PR 描述"当成交付闭环，漏了 public API 的 docs surface。sub-agent review prompt 也没有要求检查 documentation surface。

**解法**：补对应 docs 页：参数表新增字段，新增 response format 小节，写清 chunk 顺序、error chunk 格式和 curl 示例；PR body 的 Test Plan/Result 同步写入 docs check。

**怎么避免**：
1. 任何新增 public API 字段 / CLI 参数 / config key / SSE chunk schema / OpenAI-compatible 参数，提交前必须 `rg` 对应 docs，并同步文档。
2. reviewer-lens 的 Surface area audit 要包括 docs surface：新增 knob 是否有用户语义、默认值、适用条件、响应格式和错误格式文档。

---

## 2026-05-19 — 新增参数 docstring contract 和 helper 命名品味问题

**症状**：code check 后没有正确性问题，但有品味问题：(1) 新增 optional 参数后，Args docstring 没写 device/contiguous/覆盖长度/layout contract；(2) generic helper 的参数名泄漏了 caller 语义。

**根因**：实现时把注意力放在 hot path 行为和兼容 fallback 上，没把"新增内部参数"当 API surface 审；命名从调用方语境出发，没有回到 helper 所在抽象层级检查。

**解法**：把两条规则补进 `code_taste.md`：新增参数必须同步 docstring contract；generic helper 命名不能泄漏 caller-specific 语义。

**怎么避免**：
1. 任意方法新增参数（包括 internal optional fast path）都要补 docstring contract：ownership、device、contiguous、shape/layout、覆盖长度、`None` fallback。
2. helper 命名前先问"这个 helper 是 generic 还是 caller-specific"：generic helper 用抽象层级名字，专用 helper 才用调用方语义名字。
