# Claude Code Workflow Starter

源自 vLLM-Omni × HunyuanImage-3.0-Instruct 实战的 Claude Code 工作流。**直接拿去用**，不用学不用配，飞轮自动转。

## 谁该用

- 在 vLLM-Omni 上协作的同事 → clone 这个 starter + `git pull` vllm-omni 主仓库即可开发
- 做远端 GPU 调试的开发者 → 这套体系对 SSH/Slurm/Docker/Lustre 跑大模型特别强
- 任何想要"Claude 跨会话不丢失项目知识"的人 → memory + error book + 硬规则三件套

## 怎么用

### Step 1: clone 这个 starter

```bash
git clone https://github.com/zuiho-kai/claude-workflow-starter.git
```

### Step 2: 把你的项目代码放进来

```bash
cd claude-workflow-starter
git clone https://github.com/vllm-project/vllm-omni.git   # 或你自己的项目
```

就这样。CLAUDE.md / memory / .claude_errors / .claude/hooks / skills 都已经在 starter 根目录了，Claude Code 在这个目录下启动就会自动读到。

### 可选：填远端服务器信息

```bash
cp docs/remote_server.template.md docs/remote_server.md
```

然后把 `<YOUR_XXX>` 替换成你的真实信息。`docs/remote_server.md` 已在 .gitignore 里，随便写密码也不会 commit。

### 推荐：装 codex-plugin-cc

[openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc) — 装好后每次 turn 结束自动 code review，也提供 `/review` 手动审查。

---

## 这套体系怎么自动转（数据飞轮）

**不需要你手动维护**——`.claude/hooks/stop-gate.sh` 在每次 turn 结束自动跑：

```
你写代码 / 跑命令
       ↓
  Stop hook 触发
       ↓
   自动检测：
       ├─ 有代码改动？ → 提醒去远端跑测试（按 docs/remote_server.md 流程）
       └─ 有错误痕迹？ → 提醒把新坑写到 .claude_errors/（重复 ≥2 次升级到硬规则）
       ↓
   Claude 看到提醒
       ↓
   Claude 生成候选记录 → 展示 diff → 你点头确认
       ↓
   memory/ + .claude_errors/ + CLAUDE.md 自动长大
       ↓
   下次会话 Claude 自动读到这些资产
       ↓
   不会再踩同样的坑
```

**额外的自动化（skills/ 提供）**：

- `claudeception` — 数据飞轮核心：从会话自动提炼踩坑记录到 `.claude_errors/`、常识到 `memory/`，条目过多时自动按主题拆分
- `reflect-system` — Stop hook 后台从对话提取你的偏好/纠正写到 pending review（不会自动应用，因为后台进程没法跟你交互）；打 `/reflect-review` 让 Claude 列出 pending、跟你讨论 diff、确认后才应用到对应 skill
- `clean-thinking` — 遇到 `Invalid signature in thinking block` API 报错时自动修

**会话快爆时**：打 `/lastwords` 或 `/遗言`，自动生成交接文档。

`/lastwords` 会把当前会话浓缩成一份"遗言"markdown：项目背景、已完成/未完成的工作、关键决策、下一步建议、关键文件清单。标题是轻小说风格（读标题就知道会话死在哪一步）。保存到项目根目录 `遗言/` 文件夹。新会话开头 `cat 遗言/<文件名>` 就能 30 秒接手。

这是 `.claude/commands/` 里的 slash command（不是 skill），只在你手动打 `/lastwords` 时触发。

---

## 内容物

| 资产 | 用途 |
|------|------|
| `CLAUDE.md` | P1-P8 宪法 + ~50 条派生硬规则 + 项目索引 |
| `memory/` | 常识 book（~50 篇 frontmatter MD，按 feedback/remote/ci/hf 分目录）—— 跨会话项目知识 |
| `.claude_errors/` | error book —— 踩坑地册（已含 vLLM-Omni 实战 12 篇 case） |
| `docs/remote_server.md` | 脱敏版远端 GPU 服务器连接指南 |
| `.claude/commands/` | `lastwords.md` + `遗言.md`（会话交接 slash command） |
| `.claude/hooks/stop-gate.sh` | **核心自动化**：每次 turn 结束触发飞轮 |
| `.claude/settings.json` | 注册上面的 hook |
| `skills/claudeception/` | 数据飞轮自动积累：踩坑→error book，常识→memory，条目过多自动拆分 |
| `skills/clean-thinking/` | 修 thinking 块 API 报错 |
| `skills/reflect-system/` | 自动 reflect 用户纠正 |

---

## 为什么这么设计

**P1-P8 宪法** 是从 3 个月实战里提炼的 8 条不可违反原则（证据先行、简单直接、完整链路、单变量隔离、测试打真实路径、拒绝静默降级、范围自律、代码品味）。~50 条硬规则全是宪法在具体场景的派生，每条标了从哪条宪法来。

starter 把这套机制完整搬过来：**让你少踩同样的坑**。

如果你踩到了新坑（现有规则没覆盖的），hook 会自动提醒你写到 `.claude_errors/`；同坑 ≥2 次就升级到 `CLAUDE.md` 硬规则，**必须标 P1-P8 派生**。这就是飞轮自己转大的方式。

---

## 远端 GPU 调试体系

来自实战：vLLM-Omni 跨节点（SSH + Slurm + Docker + Lustre）跑 80B 模型的踩坑记录。如果你也做类似的工作，重点看：

- **CLAUDE.md** A 组规则（A1-A12）—— 远端/容器/Slurm 全覆盖
- **memory/remote/** —— `node_basics.md`（进新节点流程）、`container_setup.md`（容器持久化 + HF cache 陷阱）、`srun_lifecycle.md`（退 srun 三步走 + 偷空闲 GPU）、`ssh_workflow.md`（SSH key + retry）、`hf_offline_mandatory.md`（HF 加载必须 OFFLINE）
- **memory/feedback/** —— `remote_debug_strategy.md`（先侦察再写代码）、`execution_principles.md`（简单方案优先）
- **docs/remote_server.template.md** —— SSH/Slurm/tmux/docker 操作模板（首次使用前填 placeholder）
- **`.claude/hooks/stop-gate.sh`** —— 写完代码自动提醒去远端跑测试

---

## 要改的（少量）

- `CLAUDE.md` 宪法 P1-P8 和 B/C/D/F 组大部分规则是**通用方法论**，直接留用
- `memory/archive/hunyuan/` 是 HunyuanImage3 接入考古——当 case study 看一遍，不适用你的项目就清掉
- `memory/hf/` 里的 HF baseline 对齐方法适用于所有 `trust_remote_code` 模型，不只 HunyuanImage3
- `.claude_errors/` 里的 painterly / KV reuse 系列——当 case study 学格式，写自己的之前不要删
- **E 节（架构国策）** 是占位——按你项目的架构约束填具体规则

---

## 隐私说明

这个 starter 的飞轮机制涉及读取/落盘会话内容，对外发布前请知悉以下行为：

- **不会主动上传**：本工具不会把 SSH 密码、API token、私钥推送到任何远端。所有飞轮产出都在本地或你显式 push 的仓库里。
- **本地落盘**：`reflect-system` 会读 Claude Code 的 transcript，提取你的纠正/反馈片段（截断到 500 字符），保存到 `~/.claude/skills/reflect-system/meta/feedback-log.jsonl`。这是本地文件，不会自动 push，但要知道它在那里。
- **`.claude_errors/` 默认确认**：写入 `.claude_errors/` 之前 Claude 会展示 diff 并问你；hook 提示语只是建议，不直接落盘。如果你要更严格，把 `.claude_errors/` 也加进 `.gitignore`。
- **远端密码的存放**：放到 gitignored 的 `*.md` 实例文件（如 `docs/remote_server.md` / `memory/remote/ssh_connection_pattern.md`），**不要**写到环境变量——env var 在 `ps -ef` / `/proc/<pid>/environ` / shell history 里都能看到，反而比物理隔离的 markdown 更危险。
- **Commit 前自检**：
  ```bash
  git status --ignored                       # 看哪些文件被 gitignore 拦了
  git check-ignore -v <你担心的文件>          # 验证某文件确实被忽略
  git diff --cached | grep -iE 'password|token|<YOUR_REAL_IP>'  # 自定义 grep
  ```

---

## 故障排查

- **hook 不触发？** 检查 `.claude/settings.json` 是否在项目根；`bash -n .claude/hooks/stop-gate.sh` 验语法；`python -m json.tool .claude/settings.json` 验 JSON 格式
- **远端连不上？** 读 `docs/remote_server.md` 顶部"首次使用"表，确认 placeholder 全填了
- **API 报 `Invalid signature in thinking block`？** 打 `/clean-thinking`，自动修
- **上下文快爆？** 打 `/lastwords` 或 `/遗言`，生成交接文档后开新会话
