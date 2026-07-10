# vLLM-Omni 调试

## 什么时候查这里

- 调查任何 vLLM-Omni 仓库专有 bug、crash 或行为异常。
- 读完通用 `framework/debug/` 后必须从这里完成仓库特化路由；不要直接从通用规则跳到源码。

## 不放什么

- 通用调试纪律；先看 `framework/debug/`。

## 仓库二次路由

| 下一步要确认什么 | 查看哪里 |
|---|---|
| 配置、开发入口或仓库级实现约束 | [dev](../dev/_index.md) |
| 问题属于哪个共享源码模块 | [组件职责地图](../components/_index.md) |
| 问题是否只属于一个模型 | [模型列表](../models/_index.md) |
| 已有的仓库调试方法 | [debug guides](guides/_index.md) |

先用 current main 的入口、调用链和数据 owner 选择已有模块或模型，再读该目录的 `_index.md`、`architecture.md` 和已有 `rules.md`。一个问题跨多个位置时选择制造错误状态的 owner，其他位置只作证据。现有职责地图覆盖不了时继续查 live 源码；只有复盘证明形成了稳定、可复用的模块边界，才新增模块或更新职责地图。
