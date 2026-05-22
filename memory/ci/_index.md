# Memory · ci/

**何时来翻**：动 `tests/` 下文件、加 CI step、加 perf/accuracy 测试、新增 JSON 测试配置。做"团队同款 CI"先读 `always_inspect_existing_tests_first.md`。

| 文件 | 一句话 |
|------|--------|
| [always_inspect_existing_tests_first.md](always_inspect_existing_tests_first.md) | 做 CI 类需求先打开 `tests/` 现有文件看一眼，别基于幻觉讨论方案 |
| [ci_gotchas.md](ci_gotchas.md) | 三件套：`.gitignore` 排某类文件时新增 config 必须 `git add -f`；单阶段 pipeline 必须关 `async_chunk`；大模型 perf test 多 case 同 session OOM 应拆独立 step + soft_fail |
