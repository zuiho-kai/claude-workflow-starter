---
name: 执行原则：简单 / 直接 / 听用户的 / 持续修
description: 执行类反复犯错合集——优先简单方案、用户给方案直接执行、已知结论直接用、简短指令先还原意图、IP+port 先 probe、连环 dep 错误别 bail、Windows 文本显式 UTF-8
type: feedback
---

## 1. 优先最简单直接方案，禁止绕远路

遇到环境问题时，先检查现有环境（venv、conda）是否已经有需要的东西，有就直接用。**不要**在简单方案存在时选复杂方案（PYTHONPATH hack、pip 升级系统包、加别名 patch 等）。

**Why:** 用户原话"你为什么就是不肯用 source .venv 呢"。绕路方案不可靠（PYTHONPATH 优先级问题、遗漏依赖），还浪费时间。
**How to apply:** 远端跑框架代码前，第一步永远是 `source <YOUR_REMOTE_WORKDIR>/.venv/bin/activate`，不要 PYTHONPATH 指 `.venv/lib/...`。

**反例（cp -r 复制 venv）：** 用户说"在新节点用你自己的 new venv 跑"，我去 `cp -r <OTHER_PATH>/venv .venv` 想复制一份。错两层 —— (a) "new" 字面是 `uv venv` 新建，cp 出来的是别人 venv 状态的副本；(b) cp -r 对 venv（含 symlink / uv cache / 并行 fs）几乎一定膨胀（8.8GB → 25GB+）。**正确做法**：`uv venv .venv` + `uv pip install <framework>==X` + `uv pip install -e . --no-build-isolation`，uv wheel cache 命中后跟 cp 同速且干净。这条是 §1 反向踩坑——"复用别人 venv = 现成方案" 是错觉，**新装 = 现成方案**（uv 让 install 几乎是 O(cache lookup)）。

## 1.1 Windows 文本文件一律显式 UTF-8

在 Windows/PowerShell 里读写本仓中文文档时，默认编码会把 UTF-8 内容显示成乱码。以后打开 `CLAUDE.md`、`AGENTS.md`、`memory/`、`.claude_errors/`、`docs/` 下的文本文件，一律显式 UTF-8。

**How to apply:**
- 读文件：`Get-Content -Path <file> -Encoding utf8`
- 写文件：`Set-Content -Path <file> -Encoding utf8` / `Out-File -Encoding utf8`
- 本机已在用户级 PowerShell profile 里设置默认值：
  - `C:\Users\user\Documents\WindowsPowerShell\profile.ps1`
  - `C:\Users\user\Documents\PowerShell\profile.ps1`
- 如果只是终端显示乱码，可在当前 shell 先设：
  ```powershell
  $OutputEncoding = [System.Text.UTF8Encoding]::new($false)
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  ```
- 但 Python 环境变量（`PYTHONUTF8` / `PYTHONIOENCODING`）只影响 Python，不影响 PowerShell `Get-Content`；文件 cmdlet 仍以 profile 默认值或显式 `-Encoding utf8` 为准。

**Why:** `Get-Content CLAUDE.md` 曾把中文规则读成乱码，影响规则理解。

## 2. 用户给出明确方案时直接执行，禁止"先试试不改"

用户说 TP=2 + 减层时，**直接** TP=2 + 减层。不要先试 TP=2 不减层、OOM 后再减层。

**Why:** 远端机器时间宝贵（每轮 serve 启动+失败要几分钟）。用户比你更了解模型和硬件约束。
**How to apply:** 用户给明确技术方案 → 直接执行。不要"先试试不改看行不行"。

## 3. 已知结论直接应用，禁止重新推导

之前对话/error book/memory 已得出的结论，**直接用**，不要重新验证。

**Why:** 用户原话"为什么耗时那么久才分析出这种最简单的东西，这个之前不是已经发现过了么"。
**How to apply:** 优先行动，减少分析循环。涉及的主题在 memory 里有就先读 memory，按里面的方案执行；用户操作触发时（远端 SSH / Git / CI / 新模型接入 / 容器环境变量）先扫一眼对应的 `_index.md`，再行动。

## 4. 简短指令必须先还原完整意图再执行

用户简短指令 ≠ 字面操作。每次先用近 2-3 轮上下文还原完整意图再执行。

**Why**：多次犯同类错误：
- "push 到 X" → 按字面 push，但没意识到隐含意图是"更新已有 PR"，结果用了自造 branch 名
- "B" → 开始详细解释，被打断"搞快点"才砍——之前的 (B) 选项已经讨论过，用户选 B 就是要直接落代码

**How to apply**：
- 收到极简指令（≤5 字 / ≤2 句）时，先在内部 reconstruct："用户上一轮在做什么 → 这条指令在那个 task 链上对应什么具体动作"
- 涉及推送 / 切换 / 选择类指令尤其要查上下文：
  - "push 到 X" 一般 = 更新已存在的 PR / branch，不是新建
  - "用 B" / "走 A" = 已 evaluation 完，直接落地，不再展开论证
  - "跑" / "继续" = 已讨论过的方案立刻执行
- reconstruct 后**默认按隐含意图执行**；只在有歧义时才反问，反问要带"我猜你是想 X，对吗？"具体选项，不要敞开问

## 5. IP+port 给出来直接 SSH 探，不要先问一堆

When the user gives only `IP:port` for a remote server, **attempt SSH directly first** (defaults: `root@<ip> -p <port>` with the local default key + key-auth). Don't ask the user for username, password, or environment context until that probe actually fails.

**Why:** 用户原话（多次重复犯）"直接 ssh 就行"。问 6 个问题（username? password? GPU count? model path? venv ready? docker?）每个都是一行 `ssh '...'` 的事。

**How to apply:** First contact with a fresh remote → run `ssh -o StrictHostKeyChecking=no -p <port> root@<ip> 'hostname && nvidia-smi -L && pwd && ls'`（或类似单条合并探针）。Only ask the user when:
- SSH probe returns `Permission denied` for both publickey and password
- The user explicitly asks for help configuring the connection
- An action is irreversible / risky — that warrants confirmation regardless

任何用户**直接给出**的 IP+port = `ssh root@<ip> -p <port> '<combined probe>'` 是 FIRST action，不是先问。问题只在 `Permission denied` / 连接拒绝 / hostname 不匹配后才问，且一次只问一个具体的，不要打包六问。

## 6. 连环 dep 错误每个都是一行 sed → 继续 fix forward，别喊"系统坏了"

When a runtime stack reports compound errors (each crash reveals the next unrelated symptom), and **each individual error is a small targeted fix** (rename a kwarg, swap a submodule import, drop a dropped parameter), keep grinding through them. Don't escalate to "this is fundamentally broken" until the user actually agrees the next patch isn't worth it.

**Why:** 某次 dep-mismatch 场景，第 3 个错误出现时就喊"fundamentally broken"。用户怒怼"之前不是打死都说不行么"。其实 4 个错每个都是 1-3 行 sed：
1. import path 变更 → try/except fallback
2. 某参数被上游移除 → drop 对应 call sites
3. 某 class attribute rename → 访问新路径
4. 某 kwarg 改名 → rename call sites

四条全打完直接进真正的 model loading。"fundamentally broken" 完全是错觉。

**How to apply:**
- 2-3 个 dep-mismatch 错堆起来时，本能反应是"give up"。Override that. Each error in API/version drift chain is usually independent and small.
- Bail-trigger 应该是**行为性**不是**计数性**：actual code rewrite 需要、semantic change 需要（不是 rename/shim）、或用户明说停。
- 给 user 更新时 frame 成 "fixing forward, here's the next one"，不是 "stack is broken, options are A/B/C"。Option ladder 留给真架构性 blocker。
- 那种"compound error 看起来吓人"的反应是我自己的，不是 codebase 的。再 sed 两次再认输。
