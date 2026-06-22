# Error Book: 远端验证工作流

本页只做远端验证错题入口，具体事故内容按章节拆到 `remote_validation_workflow/`，避免单文件继续膨胀。

| 条目 | 文件 |
|------|------|
| 2026-06-17 — PR #4041 512 step-SDPA 验证复盘必须落本仓，不落个人 Codex 私有目录 | [remote_validation_workflow/001-2026-06-17.md](remote_validation_workflow/001-2026-06-17.md) |
| 2026-06-15 — PR #4041 0.23 benchmark 先跑错 workload，又把并发误报成 grouped batch | [remote_validation_workflow/002-2026-06-15.md](remote_validation_workflow/002-2026-06-15.md) |
| 2026-06-08 — 用户已指定 online start/stop，我却用 bounded smoke 替代正式 trace | [remote_validation_workflow/003-2026-06-08.md](remote_validation_workflow/003-2026-06-08.md) |
| 2026-06-08 — AR graph profiler 无界采样会杀 worker，空 trace 目录不能算成功 | [remote_validation_workflow/004-2026-06-08.md](remote_validation_workflow/004-2026-06-08.md) |
| 2026-06-08 — HunyuanImage3 AR graph 被复杂化：profiler/cache/PATH 混排导致耗时过长 | [remote_validation_workflow/005-2026-06-08.md](remote_validation_workflow/005-2026-06-08.md) |
| 2026-05-19 — 小 lint 修复不该默认上远端复验 | [remote_validation_workflow/006-2026-05-19.md](remote_validation_workflow/006-2026-05-19.md) |
| 2026-04-27 — 远端命令盲等 210s 不看日志 | [remote_validation_workflow/007-2026-04-27.md](remote_validation_workflow/007-2026-04-27.md) |
| 2026-05-18 — 跨主机同步代码用 patch/scp 走弯路，git push/fetch 才是正路 | [remote_validation_workflow/008-2026-05-18.md](remote_validation_workflow/008-2026-05-18.md) |
| 2026-05-18 — gh CLI token keyring 失效，PR 描述更新需手贴 | [remote_validation_workflow/009-2026-05-18.md](remote_validation_workflow/009-2026-05-18.md) |
| 2026-05-19 — 远端验证前没读 remote_server.md，错过指定 venv | [remote_validation_workflow/010-2026-05-19.md](remote_validation_workflow/010-2026-05-19.md) |
| 2026-05-19 — PowerShell 到 SSH 投递脚本：变量展开 / 空文件 / BOM 三连坑 | [remote_validation_workflow/011-2026-05-19.md](remote_validation_workflow/011-2026-05-19.md) |
| 2026-05-19 — 远端路径不能猜：模型 snapshot 不等于 deploy config 所在地 | [remote_validation_workflow/012-2026-05-19.md](remote_validation_workflow/012-2026-05-19.md) |
| 2026-05-19 — 测旧 PR 前先做 base commit venv/ABI smoke，别直接跑完整 profiling | [remote_validation_workflow/013-2026-05-19.md](remote_validation_workflow/013-2026-05-19.md) |
| 2026-05-19 — 新终端远端冷启动太慢：不要把已有上下文重新 discover 一遍 | [remote_validation_workflow/014-2026-05-19.md](remote_validation_workflow/014-2026-05-19.md) |
| 2026-05-20 — 同一类远端节点不能共享路径记忆 | [remote_validation_workflow/015-2026-05-20.md](remote_validation_workflow/015-2026-05-20.md) |
| 2026-05-20 — Issue 复现不能把“脚本跑完”当成“打到同一路径” | [remote_validation_workflow/016-2026-05-20.md](remote_validation_workflow/016-2026-05-20.md) |
| 2026-05-20 — PowerShell→SSH 投递脚本已知高风险时，默认用 base64 | [remote_validation_workflow/017-2026-05-20.md](remote_validation_workflow/017-2026-05-20.md) |
| 2026-05-20 — GitHub connector 可能无评论权限，先准备可粘贴正文 | [remote_validation_workflow/018-2026-05-20.md](remote_validation_workflow/018-2026-05-20.md) |
| 2026-06-01 — 远端 benchmark 脚本没有 fail-fast，会把 argparse 失败空等成“模型慢” | [remote_validation_workflow/019-2026-06-01.md](remote_validation_workflow/019-2026-06-01.md) |
| 2026-06-01 — Full IT2I benchmark 跑通后，不能把 unavailable 指标写成性能收益 | [remote_validation_workflow/020-2026-06-01.md](remote_validation_workflow/020-2026-06-01.md) |
| 2026-06-02 — Benchmark 需求被脑补成 PR3938 对比，属于 scope hallucination | [remote_validation_workflow/021-2026-06-02.md](remote_validation_workflow/021-2026-06-02.md) |
| 2026-06-02 — HunyuanImage3 AR-only 已有成功脚本，却先手写 runner 导致初始化失败 | [remote_validation_workflow/022-2026-06-02.md](remote_validation_workflow/022-2026-06-02.md) |
| 2026-06-02 — HunyuanImage3 AR profiler 不能改初始化语义，参数校验必须在启动前完成 | [remote_validation_workflow/023-2026-06-02.md](remote_validation_workflow/023-2026-06-02.md) |
| 2026-06-02 — HunyuanImage3 AR benchmark 已有可复用 runbook，禁止下次从头摸索 | [remote_validation_workflow/024-2026-06-02.md](remote_validation_workflow/024-2026-06-02.md) |
| 2026-06-05 — PR #4041 性能/精度远端验证执行失控，准备工作冒充进展 | [remote_validation_workflow/025-2026-06-05.md](remote_validation_workflow/025-2026-06-05.md) |
| 2026-06-05 — 共享 SSH 机器 graph profiling 失控：把“坚持跑出结果”误当 owner 意识 | [remote_validation_workflow/026-2026-06-05.md](remote_validation_workflow/026-2026-06-05.md) |
| 2026-06-08 — AR graph profiling 重跑时新建 cache root，制造 10 分钟 cold compile | [remote_validation_workflow/027-2026-06-08.md](remote_validation_workflow/027-2026-06-08.md) |
| 2026-06-12 — AR graph perf/profiling 返工复盘：先锁口径，再烧 GPU | [remote_validation_workflow/028-2026-06-12.md](remote_validation_workflow/028-2026-06-12.md) |
| 2026-06-12 — 10 小时 AR graph d-step 性能分析为什么失控 | [remote_validation_workflow/029-2026-06-12.md](remote_validation_workflow/029-2026-06-12.md) |
| 2026-06-16 — LTX2.3 PR #4464 性能看护验证多次跑偏 | [remote_validation_workflow/030-2026-06-16.md](remote_validation_workflow/030-2026-06-16.md) |
| 2026-06-17 — PR #4464 LTX2.3 L4 baseline 被半冷口径和 payload 漏传带偏 | [remote_validation_workflow/031-2026-06-17.md](remote_validation_workflow/031-2026-06-17.md) |
| 2026-06-22 — 远端 Hunyuan e2e 未先证明 cache 只读可复用，缺 cache 时触发重复下载风险 | [remote_validation_workflow/032-2026-06-22.md](remote_validation_workflow/032-2026-06-22.md) |
