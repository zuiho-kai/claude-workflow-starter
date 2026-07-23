# Serving 请求合同规则

- **SERV-1a — 公开字段由 serving 显式拥有。** 修改请求 allowlist 或冲突字段集时，逐项绑定真实 consumer；禁止从包含运行时状态的内部结构反射生成。验收包含一个内部同名字段，证明它不会被误算成公开 root 字段。
- **SERV-1b — 多来源输入验证前不得合并。** flattened、raw nested、声明字段和 alias 保留来源直到冲突检查结束；禁止用 `or`、字典展开或 `update()` 决定重复值。验证通过后如以字典展开构造并集，须注明各映射已经不相交，不能让展开顺序看起来像未声明的优先级合同。验收同时覆盖重复字段返回明确 4xx，以及不重叠字段到达最终 consumer。
- **SERV-1c — 入口接受必须闭环到每个生产消费者。** 对每条 dispatcher 追踪字段到 engine、pipeline、prompt 或 sampling 参数；禁止用 helper 返回值或 HTTP 成功代替传播证明。验收使用真实请求对象覆盖默认值和非默认值，并断言最终 consumer。
- **SERV-1d — 同一请求合同错误必须跨 dispatcher 保持同一响应合同。** 同一非法输入无论走 diffusion-only、multi-stage 或其他受影响 dispatcher，都必须使用一致的 status、错误类型和消息策略；禁止一路在本地映射为 4xx、另一路交给远处通用 `ValueError` 捕获。验收让同一冲突输入分别经过每条受影响 dispatcher，断言响应等价，并确认失败发生在 engine 或 pipeline 调用之前。
- **SERV-1e — 请求期弃用信号必须对 operator 可见。** serving 路径接收 deprecated 输入时，使用项目 logger 的 `warning_once`（或明确的限频策略），不要用仅写 stderr 且按调用点过滤的 `warnings.warn`。验收覆盖合法旧输入恰好记一次警告、冲突而返回 4xx 的输入不记兼容警告，并将用户响应合同与日志合同分别断言。
- **SERV-1f — 一个请求合同只能在 serving 边界编译一次。** 同一类用户输入的所有 raw ingress、默认值区分、alias、兼容字段、冲突验证和弃用事件必须由唯一的 request-contract compiler 处理，并产出可传给所有 dispatcher/stage 的规范化合同对象；dispatcher 和 stage 只能消费该对象，不能再次读取 `request`、`model_extra`、`extra_body` 或自行决定冲突、HTTP 错误和弃用日志。该 compiler 的失败必须带有统一的用户响应合同，并在公共边界转换一次。验收以每种支持的 dispatcher 运行同一组合法、冲突和 deprecated 输入，断言编译恰好一次、最终 consumer 一致、冲突响应一致、弃用日志至多一次且不会在拒绝请求时出现。
