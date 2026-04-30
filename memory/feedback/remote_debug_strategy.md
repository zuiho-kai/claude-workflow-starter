---
name: 远端调试策略：先侦察、本地试错、不走 git 部署循环
description: 2026-04-21 HunyuanImage3 tokenizer 修复用 6 轮 git commit-push-pull 才跑通，烧一天+$300。教训：调试 ≠ 部署、先侦察再写代码、tmux/docker exec 引号陷阱
type: feedback
---

## 核心原则

**git commit-push-pull 是部署手段，不是调试手段**。每轮"本地改 → push → 远端 stash → pull → run"5-10 分钟，6 轮就是 30-60 分钟。判据：你的 commit message 是 "fix attempt N" → 你在用部署流程做调试，**立刻停下来换策略**。

**正确做法**：
- 调试：远端直接写 `/tmp/test_xxx.py` 或 Python one-liner，tmux 里跑，快速迭代
- 确认方案后：回本地写正式代码，**一次** commit-push-pull 部署

## 接入新模型/新组件前必先做环境侦察

**反例（2026-04-21 tokenizer 6 轮失败链）**：
1. `AutoTokenizer.from_pretrained` → 没 `auto_map`（**没看 tokenizer_config.json**）
2. `PreTrainedTokenizerFast.from_pretrained` → transformers 版本 bug（**没查远端版本**）
3. `get_class_from_dynamic_module` → `HF_HUB_OFFLINE=1` 断网（**忘了离线约束**）
4. `snapshot_download` → symlink 解析失败（**不了解 HF cache 结构**）
5. `try_to_load_from_cache` → 依赖 `refs/main` 不存在（**同上**）
6. 手动遍历 HF cache 目录 → 成功（**应该是第 1 步**）

如果第 1 步花 5 分钟收集信息：
```bash
# 一次 SSH 全收集
cat $HF_HOME/hub/models--XXX/snapshots/*/tokenizer_config.json
ls $HF_HOME/hub/models--XXX/refs/                  # refs/main 是否存在
ls $HF_HOME/hub/models--XXX/snapshots/*/tokenizer*
pip show transformers | grep Version
python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('XXX')"
```
就能一次性发现所有阻塞点，直接跳到最终方案。

## HF cache 结构备忘

- 路径：`$HF_HOME/hub/models--{org}--{name}/snapshots/{hash}/`
- `refs/main` 可能不存在（手动下载或旧版 CLI 不创建）
- `try_to_load_from_cache(revision=None)` 依赖 `refs/main` → 不可靠
- `snapshot_download` 返回的路径可能有 symlink 问题
- **最可靠 fallback：手动遍历 snapshots/ 目录找文件**

## tmux / docker exec 陷阱

- **tmux 前台进程陷阱**：`python ... | tee log` 占住 shell，`send-keys` 发的命令进了进程 stdin。测试 API 必须从**另一个 window** 发请求
- **docker exec 跨节点引号陷阱**：`ssh nodeA "docker exec $(docker ps -q) ..."` 的 `$()` 在本地展开 → 必错。解法：写脚本到 Lustre，然后 `ssh nodeA bash /shared/path/script.sh`
- **远端发命令后必先短 sleep（≤5s）+ capture 确认脚本真启动了**（看到 pytest `collected N items` / 程序日志 / 明确错误信息），再长 sleep 等结果。光看 shell 回显不算

## Plan 拆分

Plan 按当前任务拆，不要把未来工作混进来。当前任务是 X 就只 plan X——过大的 plan 导致认知负担重 + 每次读 plan 烧 context。

## 减少 SSH 次数

每次 SSH（ASKPASS + capture-pane）~500 token，6 轮调试 × 每轮 3-5 次 = 大量浪费在重复模板。
- 合并 SSH：一次发多条命令（`&&` 或脚本）
- 减少 capture 频率：合理估算等待时间，不要频繁轮询
- 复杂操作写远端脚本一次执行
