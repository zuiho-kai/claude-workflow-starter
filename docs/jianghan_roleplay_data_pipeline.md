# 江涵 Roleplay 数据管线框架

目标目录：`D:\jianghan-roleplay-data-pipeline`

本页是 workflow-starter 侧的江涵项目入口。详细执行命令仍以目标目录内的
`CLAUDE.md`、`PLAN.md` 和 `docs/` 为准；本页吸收当前路线、硬卡点、错题本
和交接状态，避免下一轮又回到已否决的路径。

## 开工先读

在 `D:\jianghan-roleplay-data-pipeline` 做任何数据、脚本、配置、训练或文档改动前，先读：

```text
CLAUDE.md
PLAN.md
docs/stage_execution_guide.md
docs/training_data_hard_rules.md
docs/lastword_unfinished_items_2026-05-22.md
```

如果碰到具体阶段，还要读对应复盘：

```text
docs/training_reset_2026-05-22.md
docs/stage3_v1_failure_retrospective.md
docs/context_retrospective_2026-05-22.md
docs/stage3_source_routing.md
docs/stage2_worldbook_qa_mix_plan.md
```

## 当前唯一主线

```text
Qwen/Qwen3.5-4B
-> full novel CPT
-> Stage2 world QA / worldbook QA guardrails
-> Stage3 original-novel-only Jianghan narrative role base
-> Stage4 desktop assistant / secretary distillation
```

当前最重要的纠偏：

```text
Stage3 = original novel only.
```

Stage3 不是桌面聊天，也不是短台词补全。它训练“江涵在小说场景里如何观察、建模、行动、短句回应、轻叙事推进”。Stage4 才把这个角色底座压缩到读屏、聊天、工具汇报和任务下发。

## 已作废结论

上一轮远端 smoke 不能作为目标 LoRA 质量证据。

作废原因：

- 目标基座是 `Qwen/Qwen3.5-4B`，但远端当时没有完整 snapshot/权重。
- 实际训练临时用了 `Qwen2.5-7B-Instruct`，模型族、尺寸和 instruct 惯性都不一致。
- 训练混入了用户已否决的 CoSER Top100 / `roleplay_seed_top100`。
- 因此结果只能保留为脚本、远端、token chunking、device 等工程记录，不能判断江涵人格或世界观是否学会。

禁止用这些路径下结论：

```text
runs/qwen25_7b_*
diagnostics/qwen25_7b_*
data/train/jianghan_roleplay_seed_top100.jsonl
data/processed/coser_clean/roleplay_selected.top100.jsonl
runs/qwen35_4b_jianghan_role_sft_v1_scene
data/train/jianghan_scene_sft_v1.chat.jsonl
```

## 阶段职责

### Stage 1: 全本小说 CPT

目标：让模型吸收《全民魔女1994》的世界观、长期名词关系、叙事语感和世界质地。

数据形态：

```json
{"id": "novel_cpt_000001", "text": "第xxx章 ... 正文 ..."}
```

规则：

- 使用全本小说 raw text chunks，不改成问答。
- 保留章节标题和正文顺序。
- 正式训练用 `Qwen/Qwen3.5-4B` tokenizer 重新切 chunk。
- CPT 后先做世界观 / 小说续写 eval，不急着看桌面助手行为。

### Stage 2: World QA / Worldbook Guardrails

目标：世界事实、术语、组织、反幻觉护栏。

允许来源：

- 原文证据整理出的 reviewed novel QA。
- 用户批准的 SillyTavern worldbook fact QA。
- anti-hallucination QA。

禁止：

- Tavern chat logs。
- status blocks / writing prompts / visible reasoning traces。
- 把 worldbook 当 Stage3 人格反应 gold。

Stage2 v4 worldbook QA mix 约束：worldbook rows 不超过 selected source mix 的 40%，每条保留 `source_kind`、`source_id`、`evidence`、`must_not`、`review_status`。

### Stage 3: 江涵叙事角色底座

当前主线：原文-only。

输入：

```text
observed scene / latest event
```

输出：

```text
江涵中心的小说式反应：
观察 -> 内心建模 -> 动作 -> 短台词 -> 轻叙事推进
```

每条候选建议字段：

```json
{
  "id": "...",
  "mode": "stage3_narrative_role_base",
  "source_kind": "original_novel_evidence_*",
  "chapter_index": 1,
  "chapter_title": "...",
  "observed_context": "...",
  "latest_event": "...",
  "evidence_summary": "...",
  "narrative_mechanism": ["..."],
  "proposed_output": "...",
  "must_keep": ["..."],
  "must_not": ["..."],
  "review_score": null,
  "review_notes": ""
}
```

禁止作为 Stage3 主线来源：

- SillyTavern generated replies。
- CoSER transformed rows / raw ShareGPT CoSER rows。
- `mimo` / Claude / GPT 生成回复。
- old LoRA outputs。
- desktop assistant / task_report rows。

### Stage 4: 桌面助手 / 秘书蒸馏

Stage4 在 Stage3 角色底座稳定之后再做。它输出更短、更 TTS 友好、更实用。

覆盖 mode：

```text
screen_chat
screen_observe
user_chat
task_report
delegate_task
```

`task_report` 是秘书汇报，不是改写器：

- 必须保留输入事实、否定、承诺、数字、参数名、文件名和不确定性。
- 不能把 smoke 写成性能结论。
- 不能把 Claude/Codex/tool 结果改成自己做的，除非输入明确如此。
- 默认不能无依据塞入原著人物、组织、事件或设定。

## 数据硬卡点

任何 Stage3/Stage4 训练前必须有 audit report 和 review artifacts。

必查指标：

```text
row_count
output_length_min/max/avg/median
<=12_chars_ratio
<=20_chars_ratio
action_or_inner_ratio
generic_reply_count
source_kind_distribution
30 random samples
10 shortest samples
10 longest samples
10 rows from each source_kind
```

硬停止阈值：

```text
median output length < 40        -> 不准训练
<=12 chars ratio > 10%           -> 不准训练
action_or_inner_ratio < 60%      -> 不准训练角色反应 SFT
generic_reply_count > 0          -> 不准训练，先过滤或扩写
promoted train JSONL rows = 0    -> 不准训练
review_score missing            -> 不准训练
```

这些 standalone generic replies 不能作为 Stage3/Stage4 role SFT gold：

```text
嗯……
嗯。
哦。
吃。
好的。
是。
没什么。
怎么说？
这样啊。
谢谢。
```

原文短台词只能作为 evidence。若要训练，必须补齐 `evidence`、`reaction_intent` 和完整可学习 target。

## Source Role Matrix

| Source | 当前角色 | 不能做什么 |
|---|---|---|
| novel original | Stage1 CPT；Stage3 gold evidence | 不能把短原文台词自动当 SFT gold |
| SillyTavern worldbook | Stage2 QA/fact source；术语归一 | 不能当 Stage3 角色反应 gold |
| SillyTavern generated replies | out-of-band reference / diagnosis | 不能进 Stage3 主线 |
| CoSER | 历史材料、negative sample、单独批准的 auxiliary candidate | 不能 raw schema 训练；不能 Top100 自动 gold |
| mimo / Claude / GPT | Stage4 drafts 或 QA 辅助生成 | 不能做 Stage3 原文角色底座 gold |
| old LoRA output | negative sample / diagnosis | 不能当正样本老师 |

## 表达机制

江涵不是“通用 AI 助理 + 方括号 + 喵嗷”。核心机制：

```text
快速观察 -> 内心判断 -> 表面克制 -> 用短句推进现实问题
```

迁移到桌面代理：

```text
看见屏幕/听见用户 -> 判断证据够不够 -> 压住情绪接口 -> 给出下一步
```

魔女式理性：

- 情绪表达是接口层，不是决策层。
- 决策先看证据、输入、上下文和不确定性。
- 可以吐槽，但吐槽不能替代判断。
- 可以装平静、装乖、装听不懂，但不能真的不处理问题。

禁用伪江涵：

- 通用技术助理腔：“建议你先……然后……”。
- 客服安慰腔：“我理解你的担心。”。
- 空标签泄漏：“内心活动”“[内心]”“[短内心]”。
- 小剧场过量：动作和心理比事实多。
- 机械改写器腔：逐句换同义词，不做信息组织。
- 过度猫化：每条都喵嗷。

允许短、具体、和当前判断相关的内心；禁止空模板标签。

## 错题本

### 1. 用户纠偏没有立刻升级成硬约束

用户多次否定 CoSER、Top100、生成样本、短回复 target 后，旧路线仍反复回流。

以后强用户纠偏后必须写五行当前路线：

```text
Current route:
Stage:
Allowed sources:
Forbidden sources:
Output shape:
Review gate:
```

写不清就不能继续实现。

### 2. Reference quality 被误当成 training suitability

SillyTavern/worldbook prompt 运行时表现好，是因为 inference context 大，不代表它的生成回复能做 fine-tune gold。

区分：

```text
good reference != training gold
```

### 3. 原文高可信被误当成原样可训练

Stage3 v1 把原文场景压成“江涵下一句直接台词”，出现大量 `嗯……`、`吃。`、`好的。`。这些在小说里有上下文支撑，单独训练会教模型安全短答和低主动性。

正确转换：

```text
原文 evidence -> mechanism / reaction_intent -> complete narrative target
```

### 4. Stage 边界混乱

这些问题不能混在一起：

```text
模型怎么知道世界？
江涵在小说场景里怎么反应？
桌面助手怎么回答用户？
工具结果怎么汇报？
```

对应关系：

```text
Stage2 tests world facts.
Stage3 tests novel-style role reaction.
Stage4 tests desktop utility and task reporting.
```

### 5. Training 早于 review gates

训练前必须已存在：

```text
source policy documented
candidate JSONL
review markdown
review scores or explicit owner acceptance
promoted train JSONL non-empty
audit JSON/MD without hard stop
stage-matched eval JSONL
```

缺一个都不能“先训看看”。

### 6. 依赖命令被并行跑

曾经把 promote smoke 和 score-apply 并行，consumer 先跑导致输入不存在。

规则：只有独立读/独立检查可以并行；producer -> consumer 必须顺序执行。

### 7. 本地 Python 版本被假设过高

本地 Python 3.9 不支持某些新特性：

```text
zip(..., strict=True)
Path.write_text(..., newline=...)
```

脚本除非项目显式声明，否则保持 Python 3.9 兼容。至少跑一次真实脚本路径，不能只 compile。

## 当前交接状态

Stage3 narrative seed：

```text
file: data/role/jianghan_narrative_review_seed_v1.jsonl
rows: 6
status: review proposals only
source_kind: original_novel_evidence_manual_proposal
review_score: null
```

audit：

```text
file: data/role/jianghan_narrative_review_seed_v1_audit.json
row_count: 6
output_length_min: 239
output_length_median: 309
<=12_chars_ratio: 0
<=20_chars_ratio: 0
generic_reply_count: 0
hard_stop: none
```

promoted train：

```text
file: data/train/jianghan_stage3_narrative_seed_v1.chat.jsonl
rows: 0
reason: no user review scores have been applied yet
```

零行是正确状态：未审阅的行不能进训练。

下一步：

1. 让用户审 `data/role/jianghan_narrative_review_seed_v1.compact.md`。
2. 用 `0001=2,0002=1,0003=0` 形式打分。
3. `review_score = 2` 才能默认 promote 成 gold。
4. 继续构建更大的 original-novel-only Stage3 candidate set。
5. 重新 audit，无 hard stop 后才训练。

## 远端卫生

远端项目文件必须留在用户批准的项目目录下，不要散到 `/root` 或 filesystem root。

远端训练前确认：

```text
review artifacts
train data
eval data
audit report
complete Qwen/Qwen3.5-4B snapshot
```

缺完整 Qwen3.5-4B 权重时，不能用 Qwen2.5 或别的模型代替做质量结论。
