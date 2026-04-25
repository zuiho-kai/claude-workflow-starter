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
   自动执行（你点头确认）
       ↓
   memory/ + .claude_errors/ + CLAUDE.md 自动长大
       ↓
   下次会话 Claude 自动读到这些资产
       ↓
   不会再踩同样的坑
```

**额外的自动化（skills/ 提供）**：

- `claudeception` — 数据飞轮核心：从会话自动提炼踩坑记录到 `.claude_errors/`、常识到 `memory/`，条目过多时自动按主题拆分
- `reflect-system` — 自动从对话提取你的偏好/纠正 → 改进相关 skill
- `clean-thinking` — 遇到 `Invalid signature in thinking block` API 报错时自动修

**会话快爆时**：打 `/lastwords` 或 `/遗言`，自动生成交接文档。

`/lastwords` 会把当前会话浓缩成一份"遗言"markdown：项目背景、已完成/未完成的工作、关键决策、下一步建议、关键文件清单。标题是轻小说风格（读标题就知道会话死在哪一步）。保存到项目根目录 `遗言/` 文件夹。新会话开头 `cat 遗言/<文件名>` 就能 30 秒接手。

这是 `.claude/commands/` 里的 slash command（不是 skill），只在你手动打 `/lastwords` 时触发。

---

## 内容物

| 资产 | 用途 |
|------|------|
| `CLAUDE.md` | 22 条硬规则（含 worktree 约束）+ 项目索引 + Skills 表 |
| `memory/` | 常识 book（18 篇 frontmatter MD）—— 跨会话项目知识 |
| `.claude_errors/` | error book —— 踩坑地册（已含 vLLM-Omni 实战 case） |
| `docs/remote_server.md` | 脱敏版远端 GPU 服务器连接指南 |
| `.claude/commands/` | `lastwords.md` + `遗言.md`（会话交接 slash command） |
| `.claude/hooks/stop-gate.sh` | **核心自动化**：每次 turn 结束触发飞轮 |
| `.claude/settings.json` | 注册上面的 hook |
| `skills/claudeception/` | 数据飞轮自动积累：踩坑→error book，常识→memory，条目过多自动拆分 |
| `skills/clean-thinking/` | 修 thinking 块 API 报错 |
| `skills/reflect-system/` | 自动 reflect 用户纠正 |

---

## 为什么这么设计

22 条硬规则全是从"违反过 N 次"的踩坑里熬出来的——每条末尾"违反过 N 次（YYYY-MM-DD）"就是飞轮转动的痕迹。

starter 把这套机制完整搬过来：**让你少踩同样的坑**。

如果你踩到了新坑（22 条没覆盖的），hook 会自动提醒你写到 `.claude_errors/`；写够 2 次它就该升级到 `CLAUDE.md`。**这就是飞轮自己转大的方式**。

---

## 远端 GPU 调试体系

来自实战：vLLM-Omni 跨节点（SSH + Slurm + Docker + Lustre）跑 80B 模型的踩坑记录。如果你也做类似的工作，重点看：

- **CLAUDE.md** 22 条硬规则里 13 条关于远端/容器（#1-6, #8-20 大部分）
- **memory/** 里：`remote_node_general.md`、`no_container_ephemeral.md`、`srun_exit_kill_container_procs.md`、`transformers_cache_gotcha.md`、`docker_exec_cwd_workaround.md`、`feedback_remote_debug_strategy.md` 等
- **docs/remote_server.md** —— SSH/Slurm/tmux/docker 操作模板（脱敏后，首次使用前填 placeholder）
- **`.claude/hooks/stop-gate.sh`** —— 写完代码自动提醒去远端跑测试

---

## 要改的（少量）

- `CLAUDE.md` 前 21 条原硬规则全是 vLLM-Omni 实战，**保留作 case study**——用一阵后看哪些不适用你的项目，自己删
- `memory/` 里 vLLM-Omni 特有的（如 `ar_dit_bridge.md`、`bidirectional_attention.md`）—— 用一阵后清掉，留下通用的
- `.claude_errors/hunyuan_image3.md` —— 当 case study 看一遍，写自己的之前不要删（学格式）

---

## 故障排查

- **hook 不触发？** 检查 `.claude/settings.json` 是否在项目根；`bash -n .claude/hooks/stop-gate.sh` 验语法；`python -m json.tool .claude/settings.json` 验 JSON 格式
- **远端连不上？** 读 `docs/remote_server.md` 顶部"首次使用"表，确认 placeholder 全填了
- **API 报 `Invalid signature in thinking block`？** 打 `/clean-thinking`，自动修
- **上下文快爆？** 打 `/lastwords` 或 `/遗言`，生成交接文档后开新会话
