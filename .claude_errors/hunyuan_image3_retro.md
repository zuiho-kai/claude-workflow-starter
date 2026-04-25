# Error Book: feat/hunyuan-image3-accuracy-ci 整体复盘（63 commits）

从 0 搭起 HunyuanImage-3.0 的 GEBench nightly CI，累计 63 个 commit（合入 main 前 squash 成 1 个）。

## 主题 A · 方向错：先 GenEval 才改 GEBench
开工前没 `ls tests/e2e/accuracy/` 看 Qwen 怎么做，一上来写 GenEval 后推翻重写。
**提醒**：新模型接入 → diff 同类测试再动键盘。

## 主题 B · Tokenizer 加载 6 轮弯路
容器 HF cache `refs/main` symlink 丢失，6 commit 才走到 walk cache 目录。烧约一天 + $300 GPU。
**提醒**：远端 tokenizer 问题先 `python -c "..."` 一行试错。

## 主题 C · conftest fixture 三次返工
硬编码 GPU 数、漏 `--no-async-chunk`、物理/逻辑 device id 混淆。
**提醒**：新 fixture 逐条 diff 同类 fixture。

## 主题 D · smoke test 漏传 --samples-per-type
pytest 传了参数但测试函数没透传。
**提醒**：检查所有 CLI 参数是否从 fixture 透传到 benchmark 主函数。

## 主题 E · Judge GPU 选择反复调 4 次
硬编码 GPU → 被占；脚本开头选空闲卡 → 假的；残留显存 OOM。
**提醒**：GPU 选择在用的那一刻查实况；kill 后 sleep 5 确认归零。

## 主题 F · HF baseline vs Omni fairness 来回
先降 HF 到 8 step，后来发现应该升 Omni 到 28。
**提醒**：对照实验先列 checklist（steps/samples/dtype/seed/prompt/image_size）。

## 主题 G · HF cache 路径跨节点不一致
假设 `$HF_HOME/models--xxx/`，实际有 `hub/` 中间目录。
**提醒**：路径用 `find $HF_HOME -maxdepth 3 -name "snapshots" -type d` 动态查。

## 主题 H · --t2i-only 两阶段漏掉 evaluate
generate 加了 flag，evaluate 没同步。
**提醒**：多 subcommand CLI 改动全链路 grep。

## 整体教训
63 commit 里约 45 个是 bash 脚本 fix、12 个 tokenizer/fixture 修补、只有 6 个是正面前进的 feature commit。严格按规则 8 走，本 branch 应该 ≤ 10 个 commit。
