# Error Book: Git & 环境搭建

## 2026-04-08 — Rebase — untracked 文件阻塞 rebase
**症状**：`git rebase origin/main` 报 untracked files would be overwritten
**根因**：分支落后 main 269 commits，untracked 文件在新 main 里已被 track
**解法**：`git stash -u`（带 `-u`），rebase，`git stash pop`
**提醒**：rebase 前先 `git stash -u`

## 2026-04-08 — Rebase — 6 个文件内容冲突
**症状**：image_to_text.py、test_fused_moe.py、tokenizer 等全部冲突
**根因**：上游 main 也在改 hunyuan_image3 相关文件
**解法**：按文件归属选 ours/theirs
**提醒**：rebase 前 `git log origin/main --oneline -- '**/hunyuan*'` 看上游有没有动过同名文件

## 2026-04-08 — Git — 代理格式错误
**症状**：`git push` 报 `Unsupported proxy syntax`
**根因**：代理地址缺 `http://` 前缀 + 尾部空格
**解法**：`https_proxy="http://127.0.0.1:7890"` 显式指定
**提醒**：代理必须带协议前缀

## 2026-04-08 — gh CLI — 代理不生效
**症状**：`gh repo fork` 报 `error connecting to http`
**根因**：gh CLI 不走 http_proxy 环境变量
**解法**：fallback 到 `curl --proxy` + GitHub API
**提醒**：gh CLI 网络不可靠时用 curl

## 2026-04-08 — GitHub — user is blocked
**症状**：创建 PR 返回 `user is blocked`
**根因**：`<YOUR_GITHUB>` 账号被仓库屏蔽
**提醒**：push 到 fork 成功 ≠ 能往上游提 PR
