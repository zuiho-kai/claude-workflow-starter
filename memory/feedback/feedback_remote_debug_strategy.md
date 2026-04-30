---
name: Remote Debug Strategy - Stop Committing Every Attempt
description: 远端调试不要每次都走 git commit-push-pull，先在远端快速试错，只提交最终方案
type: feedback
originSessionId: 4cc65e60-2b58-4a9f-9d4e-5bd1dffdc6b7
---
## 事件：tokenizer 修复 6 轮 git 循环，一天时间 + $300 token 费（2026-04-21）

### 问题 1：调试策略根本性错误

用户说"不要手动改，提到仓库远端下载"是指**最终方案**的部署方式。但我把它当成了**每次调试迭代**的方式：

- 本地改代码 → git add → commit → push → 远端 stash → pull → stash pop → run → 看日志 → 失败 → 重来
- 6 轮 × 每轮 5-10 分钟 = 30-60 分钟纯等待
- 6 轮 × 每轮大量 SSH/tmux/capture context = 烧掉大量 token

**正确做法**：在远端直接用 Python one-liner 或小脚本快速试错，确认方案可行后，再回本地写正式代码提交一次。

```bash
# 远端快速验证 tokenizer 加载（30 秒搞定）
tmux send-keys -t <YOUR_TMUX_SESSION>:0 "python -c \"
from transformers import AutoTokenizer
try:
    t = AutoTokenizer.from_pretrained('tencent/HunyuanImage-3.0-Instruct', trust_remote_code=True)
    print('OK')
except Exception as e:
    print(f'FAIL: {e}')
\"" Enter
```

这样 5 分钟内就能试完所有 6 种方案，而不是 6 轮 git 循环。

**Why:** git commit-push-pull 是部署手段，不是调试手段。调试阶段追求的是快速反馈，不是代码整洁。

**How to apply:** 
- 调试阶段：远端直接写临时脚本 `/tmp/test_xxx.py`，tmux 里跑，快速迭代
- 确认方案后：回本地写正式代码，一次 commit-push-pull 部署
- 判断标准：如果你要 commit 的消息是 "fix attempt N"，说明你在用部署流程做调试，停下来换策略

### 问题 2：没有做 Pre-mortem

开始前没有列出所有可能的阻塞点。如果花 5 分钟先跑：
```bash
# 一次 SSH 收集所有信息
cat $HF_HOME/hub/models--tencent--HunyuanImage-3.0-Instruct/snapshots/*/tokenizer_config.json
ls $HF_HOME/hub/models--tencent--HunyuanImage-3.0-Instruct/refs/
ls $HF_HOME/hub/models--tencent--HunyuanImage-3.0-Instruct/snapshots/*/tokenizer*
pip show transformers | grep Version
python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('tencent/HunyuanImage-3.0-Instruct')"
```
就能一次性发现：没有 auto_map、没有 refs/main、有 tokenizer.json、transformers 版本。直接跳到最终方案。

**How to apply:** 新模型接入前，先写一个"环境侦察脚本"一次性收集所有信息，再决定方案。

### 问题 3：Plan 太大导致混淆

Plan 文档混合了 IT2I gap 分析、GenEval、GEBench、pipeline registry 等多个主题。实际任务只是"让 serve 跑起来"。过大的 plan 导致：
- 混淆了 GenEval 和 GEBench（被用户纠正）
- 认知负担重，注意力分散
- 每次读 plan 消耗大量 context token

**How to apply:** Plan 按当前任务拆分，不要把未来工作混进来。当前任务是 X，就只 plan X。

### 问题 4：SSH 操作的 token 成本

每次 SSH 操作需要：创建 ASKPASS 脚本 + SSH 命令 + sleep + capture-pane。这套模板每次 ~500 token，6 轮调试 × 每轮 3-5 次 SSH = 大量 token 浪费在重复模板上。

**How to apply:** 
- 合并 SSH 操作：一次 SSH 发多条命令，用 `&&` 或写脚本
- 减少 capture-pane 频率：发命令后合理估算等待时间，不要频繁轮询
- 复杂操作写成远端脚本一次执行，不要逐条发
