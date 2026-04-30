---
name: Always inspect existing team tests before proposing new solutions
description: 做"团队同款 CI/测试"类需求时，第一件事是打开现有测试文件看一眼，不是讨论方案
type: rule
---

# 规则：先看现有代码，再谈方案

## 反面教训（2026-04-21）

做 HunyuanImage-3 精度 CI 时，我绕了一大圈：
- 提议 GenEval + mmdet → mmcv 在 Py3.12 装不上 → 建独立 venv → 讨论怎么接 buildkite
- 讨论"用 CLIP-score 替代"、"改 GenBench 砍 it2i"、"采集 9 小时 baseline"
- 写了 300 行方案对比文档

结果用户直接去看仓库：
```
tests/e2e/accuracy/test_gebench_h100_smoke.py
```
**已经存在**，跑的就是 type3/type4 T2I，用 `/v1/images/generations`，judge 是 VLM-as-judge（Qwen2.5-VL-7B-Instruct），**零 mmdet/mmcv 依赖**。

`--gebench-model` 还是 CLI 参数。加一行 `--gebench-model Tencent/HunyuanImage-3.0-Instruct` 就能跑。

我前面所有工作（踩 mmcv 坑、建 Py3.10 venv、写 GenEval 集成代码）全部白做。

## 原则

**"团队同款 CI / 同款测试 / 同款 pattern"类需求，第一件事**：

1. 打开 `tests/` 目录看文件名
2. 找**语义最接近**的现有测试（model 换一下就能复用的）
3. 读它的 conftest fixture、CLI option、运行方式
4. **考虑能不能直接复用 / 复制一份改名**

**把这 3 步做完再开始讨论方案**。不做这 3 步的方案讨论都是空想，容易导致：
- 重复造轮子
- 引入团队没用过的依赖（reviewer 不信任）
- 方案复杂度远高于必要

## 具体到 vllm-omni 精度 CI 的文件清单（2026-04-21 查证）

| 目录 | 内容 |
|---|---|
| `tests/e2e/accuracy/` | 所有精度 CI 入口 |
| `tests/e2e/accuracy/conftest.py` | fixture 和 CLI option（`--gebench-model`, `--gedit-model`, `--accuracy-judge-model` 等） |
| `tests/e2e/accuracy/test_gebench_h100_smoke.py` | T2I 精度（type3/type4）用 VLM judge |
| `tests/e2e/accuracy/test_gedit_bench_h100_smoke.py` | IT2I 精度，同款 judge 路径 |
| `tests/e2e/accuracy/helpers.py` | `reset_artifact_dir` 等 |
| `vllm_omni/benchmarks/accuracy/text_to_image/gbench.py` | GEBench 实现（type3/type4 走 `/v1/images/generations`，type1/2/5 走 `/v1/images/edits`） |

## 下一次做新模型精度 CI

抄 `test_gebench_h100_smoke.py`，改 `--gebench-model` 参数。完成。
**除非有强理由**（比如新模型 T2I endpoint 不同、判据不同），否则不要考虑 GenEval / CLIP-score / 自研评分器。

## 判据模板

用户问"做 XX 精度 CI"时，先回答 3 个问题再提方案：
1. 团队现有类似测试文件？叫什么名字？
2. 它的 fixture 和 CLI option 我的模型能复用吗？
3. 跑一下 `pytest --gebench-model <my-model>` 会发生什么？报错才说明需要改，没报错就结束了
