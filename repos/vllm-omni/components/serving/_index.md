# Serving

- 主要源码入口：`vllm_omni/entrypoints/` 以及当前版本对应的 engine/serving 实现
- 主要职责：用户入口、请求解析、在线服务和 engine 边界

## 什么时候查这里

- CLI、HTTP、OpenAI-compatible API 或 offline/online 请求行为不一致。
- 参数在入口处丢失、默认值改变，或请求没有进入预期 engine 路径。

## 不放什么

- 模型内部 attention、checkpoint 或 diffusion 算法问题。
- 通用 API 设计方法；这些放 `framework/review/`。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 理解入口到 engine 的边界 | [architecture](architecture.md) |
| 修改请求字段、兼容输入、冲突检查或参数传播 | [rules](rules.md) |
| Request-extra 修复扩张成完整 compiler、边界校验后下游仍重读 raw request、reviewer 修复反复扩张或测试减法声明与净 diff 不符 | [serving 错题](incidents/_index.md) |
