# Error Book: CI & 测试

## 2026-04-22 — GEBench test 未传 --samples-per-type
**症状**：pytest 传了参数但测试函数没透传，跑了全量数据集
**解法**：测试函数接收 fixture 并传给 `gbench_main`
**提醒**：GEBench 每样本 6 张图，smoke test 用 `--samples-per-type 1`

## 2026-04-25 — CI dummy guard 未实际执行导致 property 运行时错误
**症状**：`AttributeError: property 'device' of 'HunyuanImage3Pipeline' object has no setter`
**根因**：只跑了 `compileall`，没让新增测试函数实际执行；`object.__new__` 绕过初始化后直接写只读 property
**解法**：`monkeypatch.setattr(HunyuanImage3Pipeline, "device", property(lambda self: torch.device("cpu")), raising=False)`
**提醒**：`compileall` 不算行为验证；用 `object.__new__` 时先确认属性不是只读 property

## 2026-04-27 — DiffusionPipelineProfilerMixin.stage_durations 无 setter
**症状**：`AttributeError: property 'stage_durations' of 'HunyuanImage3Pipeline' object has no setter`
**根因**：`stage_durations` 只读 `@property`，getter 依赖 `_profiler_lock`（只有 `setup_diffusion_pipeline_profiler` 才初始化）；`object.__new__` 裸实例两个问题叠加
**解法**：加 `@stage_durations.setter`（懒初始化）；getter 加 `hasattr` 守卫
**提醒**：新增 Mixin property 先问：测试能不能直接赋值？这是同类问题第二次
