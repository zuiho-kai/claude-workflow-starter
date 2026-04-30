# Memory · ci/

**何时来翻**：动 `tests/` 下文件、加 CI step、加 perf/accuracy 测试、新增 JSON 测试配置。做"团队同款 CI"先读 `always_inspect_existing_tests_first.md`。

| 文件 | 一句话 |
|------|--------|
| [always_inspect_existing_tests_first.md](always_inspect_existing_tests_first.md) | 做 CI 类需求先打开 `tests/` 现有文件看一眼，别基于幻觉 |
| [ci_hunyuan_perf_isolation.md](ci_hunyuan_perf_isolation.md) | Hunyuan perf test 独立 step + soft_fail + env gate 模式 |
| [ci_gitignore_json.md](ci_gitignore_json.md) | `.gitignore` 有 `*.json`，新增 JSON test config 必须 `git add -f` |
| [async_chunk_default_gotcha.md](async_chunk_default_gotcha.md) | 单阶段 diffusion pipeline 必须 `async_chunk: false` |
