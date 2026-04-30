---
name: Tokenizer Debug Retrospective
description: HunyuanImage3 tokenizer 修复经历 6 轮迭代的反思，远端调试效率教训
type: feedback
originSessionId: 4cc65e60-2b58-4a9f-9d4e-5bd1dffdc6b7
---
## 事件：HunyuanImage3 tokenizer 加载修复，6 轮 commit-push-pull-run 才跑通（2026-04-21）

### 根因：没有先侦察就动手写代码

6 次尝试的失败链：
1. `AutoTokenizer.from_pretrained` → 没 `auto_map`（没看 tokenizer_config.json）
2. `PreTrainedTokenizerFast.from_pretrained` → transformers 版本 bug，`vocab_file=None` 崩（没查远端 transformers 版本）
3. `get_class_from_dynamic_module` → `HF_HUB_OFFLINE=1` 断网（忘了离线约束）
4. `snapshot_download` → symlink 解析失败（不了解 HF cache 结构）
5. `try_to_load_from_cache` → 依赖 `refs/main` 但不存在（同上）
6. 手动遍历 HF cache 目录 → 成功

**第 6 次方案是最简单的，本应是第 1 次。**

### 浪费的时间

每轮：本地改 → commit → push → 远端 stash → pull → stash pop → run → 看日志 ≈ 5-10 分钟。
6 轮 ≈ 30-60 分钟远端机器时间。

### 教训

**Why:** 远端调试每轮迭代成本极高（网络延迟 + 模型加载 + 日志传回）。盲目试错是最贵的调试方式。

**How to apply:**

1. **写代码前先侦察目标环境**：
   - 新模型先 `ls` 模型目录看有什么文件
   - 读 `tokenizer_config.json` / `config.json` 看关键字段（`auto_map`、`tokenizer_class`）
   - 查 HF cache 的 `refs/` 目录是否存在
   - 查远端 `pip show transformers` 版本
   - 这些信息一次 SSH 就能全拿到

2. **HF cache 结构备忘**：
   - 路径：`$HF_HOME/hub/models--{org}--{name}/snapshots/{hash}/`
   - `refs/main` 可能不存在（手动下载或旧版 CLI 不创建）
   - `try_to_load_from_cache(revision=None)` 依赖 `refs/main` → 不可靠
   - `snapshot_download` 返回的路径可能有 symlink 问题
   - **最可靠的 fallback：手动遍历 snapshots/ 目录找文件**

3. **减少远端迭代次数**：
   - 能本地验证的逻辑先本地跑（比如 tokenizer 加载逻辑可以用任意 HF 模型本地测）
   - 一次 SSH 多收集信息，不要一个问题一次 SSH
   - 如果第 2 次还失败，停下来想清楚再动手，不要继续盲试

4. **tmux 前台进程陷阱**：
   - `python ... | tee log` 占住 shell，tmux send-keys 发的命令进了进程 stdin，不会被 shell 执行
   - 测试 API 必须从另一个 window/session 发请求
   - 或者用 `&` 后台运行 serve，但要注意日志收集

5. **跨节点 docker exec 引号陷阱**：
   - `ssh nodeA "docker exec $(docker ps -q) ..."` 的 `$()` 在本地展开
   - 解法：写脚本到共享文件系统（Lustre），然后 `ssh nodeA bash /shared/path/script.sh`
