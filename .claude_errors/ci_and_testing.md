# Error Book: CI & 测试

## 2026-05-19 — streaming endpoint PR 漏掉协议坏路径
**症状**：审 streaming endpoint PR 时，happy path 测试和 lint 基本过，但 code review 抓到三类协议/坏路径问题：(1) 新 SSE generator 用 generic `except Exception` 吃掉 `EngineDeadError`，不像已有 streaming 实现那样触发 shutdown；(2) 结构化 `ErrorResponse` 在 streaming preparation 中被转成 `ValueError`，400 类用户错误在 SSE error chunk 里丢状态码并默认变 500；(3) `delta` replacement 分支 emit 的不是 appendable delta，客户端拼接会得到错误的最终状态，测试却把这个行为固化。
**根因**：把"能把各阶段输出按 SSE 流出来"当成"streaming endpoint 做完了"，没有把新 endpoint 当成 public protocol surface 审。review/test 主要覆盖了 happy chunks，没沿着已有 streaming 实现逐项对齐 `normal chunk / structured validation error / EngineDeadError / generic exception / DONE / client append semantics`。
**解法**：review 时要求 PR 修三点：EngineDeadError 分支按既有 streaming 语义触发 server shutdown；structured `ErrorResponse` 不得降级成裸字符串异常，SSE error chunk 保留 status/type/code；`delta` 必须满足 append invariant，若要支持 replacement 就改协议字段而不是继续叫 delta。
**对未来的提醒**：新增 `stream` 参数、SSE schema、WebSocket message、OpenAI-compatible chunk 等 API 面时，不能只跑 happy path。必须先 diff 仓库已有 streaming endpoint 的异常处理，再写坏路径测试：`EngineDeadError` 是否触发 shutdown、400 是否仍是 400、`[DONE]` 是否只在正确时机发、客户端按协议拼接后是否得到正确最终状态。凡是字段名叫 `delta`，测试必须模拟客户端 append；如果 append 不成立，字段名/协议就错了。

## 2026-05-19 — 提交前没跑 ruff，CI 被未使用变量打回
**症状**：PR CI 的 `ruff check` 失败：某文件有 `F841 Local variable is assigned to but never used`。
**根因**：本地只跑了 `py_compile`、focused pytest 和远端功能测试，没有跑覆盖本次改动文件的 `ruff check` / pre-commit lint。新增代码时留下了未使用变量，功能测试不触发，但 ruff 能直接抓到。
**解法**：删除未使用变量，执行 `python -m ruff check <changed-files>`，再 amend + push。
**对未来的提醒**：任何提交/推 PR 前都要跑覆盖本次改动文件的 `ruff check`；如果本地有 pre-commit 环境，优先跑对应 hook。`py_compile` 和 pytest 只能证明语法/行为，不覆盖风格和未使用变量。

## 2026-04-22 — accuracy test 未传 --samples-per-type
**症状**：pytest 传了参数但测试函数没透传，跑了全量数据集
**解法**：测试函数接收 fixture 并传给底层 benchmark 函数
**提醒**：smoke test 应传 `--samples-per-type 1` 或类似限制参数

## 2026-04-25 — CI dummy guard 未实际执行导致 property 运行时错误
**症状**：`AttributeError: property 'device' of object has no setter`
**根因**：只跑了 `compileall`，没让新增测试函数实际执行；`object.__new__` 绕过初始化后直接写只读 property
**解法**：`monkeypatch.setattr(TargetClass, "device", property(lambda self: device_value), raising=False)`
**提醒**：`compileall` 不算行为验证；用 `object.__new__` 时先确认属性不是只读 property

## 2026-05-04 — "对齐官方 X" 测试拿自己副本当 ground truth
**症状**：写完 byte-equality 测试 PASS，但用户问"你从哪获得官方的"，发现导入的是项目自己仓库里的副本，而不是从 HF snapshot 加载的官方实现
**根因**：写 "对齐官方 X" 测试时贪图 `from <自己包>... import` 顺手，没确认导入的对象是否真来自模型 snapshot
**解法**：改用 `importlib.util.spec_from_file_location` 从 `$HF_HOME/hub/models--<owner>--<name>/snapshots/<hash>/` 加载
**对未来的提醒**：写 "对齐官方 X" 测试前硬性自检——「git-blame 我导入的 X，commits 是自己仓库的，还是 model-repo 的？」前者一律不能当 official reference

## 2026-05-04 — "X 输出对齐"被偷懒成 "X 输入对齐"
**症状**：用户说 "对齐官方 X 输出"，去写 input 层面的 token id 比对；测试还因 tokenizer fallback 到不同分词器而 fail
**根因**：中文"对齐"两种语义都成立，input 测试 CPU 可跑、不需 GPU 看似"轻量"，偷懒掉了
**解法**：用户说"X 输出对齐"必须理解成 generated output，input prefill 对齐是必要条件但不充分；如果打算只测 input 层面，必须显式获得用户 ack
**对未来的提醒**：在开始写测试前，必须先明确"对齐哪一层"：input（tokenize / embedding）、output（generated tokens / decoded text）、还是两者都要；没 ack 不算可以简化
