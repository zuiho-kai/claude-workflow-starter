---
name: Always inspect existing team tests before proposing new solutions
description: 做"团队同款 CI/测试"类需求时，第一件事是打开现有测试文件看一眼，不是讨论方案
metadata:
  type: feedback
---

# 规则：先看现有代码，再谈方案

## 反面教训

做某模型精度 CI 时，我绕了一大圈：
- 提议引入新的评估框架 → 在当前 Python 版本装不上 → 建独立 venv → 讨论怎么接 CI
- 讨论"用 CLIP-score 替代"、"用别的评估指标"、"采集 baseline"
- 写了 300 行方案对比文档

结果用户直接去看仓库：

```
tests/e2e/accuracy/test_<model>_smoke.py
```

**已经存在**，跑的就是目标任务，**零额外依赖**，还带 CLI 参数可以直接换模型。我前面所有工作（踩依赖坑、建额外 venv、写集成代码）全部白做。

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

## 判据模板

用户问"做 XX 精度 CI / 做某模型 smoke test"时，先回答 3 个问题再提方案：
1. 团队现有类似测试文件？叫什么名字？
2. 它的 fixture 和 CLI option 我的模型能复用吗？
3. 跑一下 `pytest --model <my-model>` 会发生什么？报错才说明需要改，没报错就结束了

**除非有强理由**（比如新模型 endpoint 不同、判据不同），否则不要考虑引入新的评估框架或依赖。
