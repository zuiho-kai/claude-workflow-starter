# Claude Code Workflow Starter

一个**通用的 Claude Code 工作流模板**：宪法 + 60+ 条硬规则 + 飞轮自动积累。**直接拿去用**，不用学不用配，飞轮自动转。

## 谁该用

- 想要 "Claude 跨会话不丢失项目知识" 的人 → memory + error book + 硬规则三件套
- 做远端 GPU 调试的开发者 → 对 SSH/Slurm/Docker/共享 FS 跑大模型的踩坑都覆盖
- 团队想把"踩过的坑"沉淀成可复用资产 → 飞轮自动转大不靠人工维护

## 怎么用

### Step 1: clone 这个 starter

```bash
git clone https://github.com/zuiho-kai/claude-workflow-starter-public.git
```

### Step 2: 把你的项目代码放进来

```bash
cd claude-workflow-starter-public
git clone <your-project-repo>
```

`CLAUDE.md` / `memory/` / `.claude_errors/` / `.claude/hooks/` / `skills/` 已经在 starter 根目录，Claude Code 在这个目录下启动就会自动读到。

### Step 3: 填项目国策（CLAUDE.md E 节）

CLAUDE.md 的「E. 架构国策」是占位，填你项目的硬性架构约束（"改 X 不改 Y" / "新增 op 必先 grep Z" 这类）。比通用规则更高优先级，会被 Claude 优先遵守。

### Step 4: 填远端服务器信息（如果用远端 GPU）

```bash
cp docs/remote_server.template.md docs/remote_server.md
```

把 `<YOUR_XXX>` 替换成你的真实信息。`docs/remote_server.md` 已在 `.gitignore` 里，随便写密码也不会 commit。

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
| `CLAUDE.md` | 宪法 P1-P8 + 60+ 条硬规则（A 远端 / B 调试 / C CI / D Git / E 项目占位 / F 编码）+ 索引 |
| `memory/` | 常识 book —— 跨会话方法论（按主题分子目录，见 `memory/MEMORY.md`） |
| `.claude_errors/` | error book —— 踩坑地册（开仓时附带通用 case，你踩到坑写进去；飞轮自动积累） |
| `docs/remote_server.template.md` | 远端 GPU 服务器连接指南模板（首次复制为 `remote_server.md` 后填） |
| `.claude/commands/` | `lastwords.md` + `遗言.md`（会话交接 slash command）+ `reflect-review.md` |
| `.claude/hooks/stop-gate.sh` | **核心自动化**：每次 turn 结束触发飞轮 |
| `.claude/settings.json` | 注册上面的 hook |
| `skills/claudeception/` | 数据飞轮自动积累：踩坑→error book，常识→memory，条目过多自动拆分 |
| `skills/clean-thinking/` | 修 thinking 块 API 报错 |
| `skills/reflect-system/` | 自动 reflect 用户纠正 |

---

## 为什么这么设计

**宪法 → 硬规则 → memory/errors 三层**：

- 宪法 8 条（P1-P8）是 why 层，规则未覆盖的新场景先回这层推
- 60+ 条硬规则是 P1-P8 在具体场景的派生，每条标注 `[Pn 派生]` 双向可查
- memory / .claude_errors 是 rationale + 实战案例库，规则末尾的链接点过去

**飞轮自带升级路径**：

- 第一次踩坑 → 写到 `.claude_errors/<topic>.md`
- 第二次踩同坑 → 升级到 `memory/<topic>.md` 作为常识
- 第三次或者影响范围大 → 升级到 `CLAUDE.md` 硬规则（**必须标 P1-P8 派生**）

这就是飞轮自己转大的方式。

---

## 远端 GPU 调试体系

如果你做远端 GPU 调试（SSH + Slurm + Docker + 共享 FS 跑大模型），重点看：

- **CLAUDE.md A 节**（A1-A12）—— 远端 / 容器 / Slurm 全覆盖
- **`memory/remote/`** —— `node_basics.md`（进新节点流程）、`container_setup.md`（容器持久化 + HF cache 陷阱）、`srun_lifecycle.md`（退 srun 三步走）、`ssh_workflow.md`（SSH key + retry）、`hf_offline_mandatory.md`（HF 加载必须 OFFLINE）
- **`memory/feedback/remote_debug_strategy.md`** —— 远端调试方法论
- **`docs/remote_server.template.md`** —— SSH/Slurm/tmux/docker 操作模板（首次使用前填 placeholder）
- **`.claude/hooks/stop-gate.sh`** —— 写完代码自动提醒去远端跑测试

---

## 隐私说明

这个 starter 的飞轮机制涉及读取/落盘会话内容，对外发布前请知悉以下行为：

- **不会主动上传**：本工具不会把 SSH 密码、API token、私钥推送到任何远端。所有飞轮产出都在本地或你显式 push 的仓库里。
- **本地落盘**：`reflect-system` 会读 Claude Code 的 transcript，提取你的纠正/反馈片段（截断到 500 字符），保存到 `~/.claude/skills/reflect-system/meta/feedback-log.jsonl`。这是本地文件，不会自动 push，但要知道它在那里。
- **`.claude_errors/` 默认确认**：写入 `.claude_errors/` 之前 Claude 会展示 diff 并问你；hook 提示语只是建议，不直接落盘。如果你要更严格，把 `.claude_errors/` 也加进 `.gitignore`。
- **远端密码的存放**：放到 gitignored 的 `*.md` 实例文件（如 `docs/remote_server.md`），**不要**写到环境变量——env var 在 `ps -ef` / `/proc/<pid>/environ` / shell history 里都能看到，反而比物理隔离的 markdown 更危险。
- **Commit 前自检**：
  ```bash
  git status --ignored                       # 看哪些文件被 gitignore 拦了
  git check-ignore -v <你担心的文件>          # 验证某文件确实被忽略
  git diff --cached | grep -iE 'password|token|<你的真实 IP>'  # 自定义 grep
  ```

---

## 故障排查

- **hook 不触发？** 检查 `.claude/settings.json` 是否在项目根；`bash -n .claude/hooks/stop-gate.sh` 验语法；`python -m json.tool .claude/settings.json` 验 JSON 格式
- **远端连不上？** 读 `docs/remote_server.md` 顶部"首次使用"表，确认 placeholder 全填了
- **API 报 `Invalid signature in thinking block`？** 打 `/clean-thinking`，自动修
- **上下文快爆？** 打 `/lastwords` 或 `/遗言`，生成交接文档后开新会话
