# Serving 错题

只有命中相似症状或需要历史证据时才查本页；正常开发仍从上级 `_index.md`、`rules.md` 和 `architecture.md` 开始。

| 症状 | 查看哪里 |
|---|---|
| Request-extra 修复扩张成完整 compiler、边界校验后 consumer 又重读 raw request、reviewer 逐 scope 加分支，或声称测试减量但净 diff 仍增长 | [request-contract patch pile](2026-07-23-request-contract-patch-pile.md) |
