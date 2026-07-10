# Model Executor 规则

## Stage 并行度和设备容量必须一起验收

- 触发条件：修改或排查全局 CLI、per-stage override、deploy YAML、平台 overlay、stage 并行度、`runtime.devices`、设备映射或 worker 启动。
- 必须做：沿公开入口展开配置合并，记录每个 stage 最终生效的 TP、PP、DP 和其他会增加 local world size 的并行参数，以及解析后的设备列表；在创建底层 worker 前校验所需设备数不超过该 stage 的可见设备数。
- 禁止：不能只证明并行参数和设备参数各自解析正确；不能截断设备列表或用 fallback 继续；best-effort 的锁、清理、日志和观测代码不能吞掉配置、拓扑或容量错误。
- 验收：至少有一个从全局参数加 per-stage override 进入最终配置的负向测试。并行 world size 大于解析后设备数时，测试必须在 worker 创建前失败，并在错误中报告 stage、并行参数、所需设备数和实际设备列表；匹配的配置必须保留原有启动行为。
