# Request-extra normalization 扩张成完整 compiler，并在边界后重读请求

- 编号：`inc-2026-07-23-request-contract-patch-pile`
- 归属：`repos/vllm-omni/components/serving`
- 状态：已提炼
- 搜索词：request extras、consumer view、raw request、nested or root、compiler scope、negative_prompt、测试减法
- 影响范围：Chat diffusion 请求字段、pure diffusion、mixed stage、AR sampling metadata

## 准入理由

- `RULES_DONE`：多来源校验、最终 consumer、RFC slice 边界、来源矩阵和膨胀硬停分别进入 `SERV-1b`、`SERV-1c`、`SERV-1f`、`SERV-1g`、`SERV-1h`；稳定数据流进入 serving architecture。
- `UNPRESERVED_EVIDENCE`：Git 能保存每次修改，但不能直接说明为什么“single owner”被误解成完整 request compiler，也不能说明为什么边界校验正确后仍会在最终 consumer 丢字段。
- `FUTURE_QUERY`：Request-extra 修复开始吸收 topology、模型能力或逐 stage 职责，或者边界测试通过但 pure/mixed 最终结果仍丢 root 字段时，查询本页。

## 当时在做什么

RFC PR1 的目标是规范化 Chat diffusion 请求的 canonical `extra_args`、legacy `extra_params`、flattened root 和 raw nested compatibility 输入，并把结果交给既有 serving 路径。

实现过程中，每次 reviewer 发现一个真实遗漏，就把更多相邻职责吸进同一个对象：root sampling fields、controls、stage defaults、per-stage overrides、topology、model capability 和 pure/mixed dispatcher。局部修复都合理，但合起来已经从“request-extra normalization”变成“编译完整 Chat diffusion 请求”。

## 看到了什么

### Scope 先扩张，后来又收窄

中间方案出现过全请求 plan、stage assignment、topology context 和 capability validation。它们试图用一个最终 plan 消除多 owner，却超过 RFC PR1 所需行为。继续拆 helper 只会重新排列职责，不能解决 scope 已经扩大。

正确纠偏不是把完整 compiler 写得更漂亮，而是恢复 RFC slice：normalizer 只拥有 extra 来源、alias、重复和兼容输入；现有 topology、capability、per-stage 和 defaults owner 保持不变。

### 边界校验后，下游又重读 raw request

Serving 边界已经分别提取 root 和 nested 来源并完成冲突检查，但 pure、mixed 和 AR sampling helper 仍使用类似：

```python
getattr(request, "extra_body", None) or request.model_extra
```

这不是合并，而是二选一。只要 nested `extra_body` 非空，flattened root 的 `num_inference_steps`、`size`、`negative_prompt` 等字段就会消失。边界 normalizer 单测可以全部通过，最终 prompt 或 sampling params 仍然错误。

### Registry 和 service control 出现双 owner

真实 model registry 可能声明 `negative_prompt`，而 serving 也把它作为 prompt control 消费。如果 declared extras 和 service controls 不先做 owner subtraction，同一个 root 值会同时登记成两份来源，被误报为 duplicate，或者进入两个不同 consumer。

### 测试绑定 helper，而不是生产入口

旧测试分别验证尺寸解析和 `_apply_request_overrides` 注入，却没有把 root control + nested extras 的真实 `ChatCompletionRequest` 送进 pure/mixed 公共入口并断言最终 prompt、AR metadata 和 diffusion sampling params。Helper 职责迁移后，继续保留这些测试只会锁住旧结构。

## 真正原因

1. **把 single owner 理解成“合并所有相邻职责”。** 正确含义应是当前 RFC slice 内的语义只有一个 owner；它不授权扩大 slice。
2. **来源矩阵没有走到最终 consumer。** 只列 ingress 和 normalizer，没有列 pure prompt、mixed prompt、AR metadata 与 diffusion sampling consumer。
3. **Reviewer finding 被串行补丁化。** 每个 finding 单独加逻辑，没有在第二个同类遗漏出现时重新确认 scope 和 owner。
4. **Diff 未冻结就开始完整验证和 sub-agent review。** 后续小改动让完整测试和独立审查重复执行，延长了交付时间。
5. **测试数量掩盖了责任重复。** 多个 helper test 看似覆盖丰富，但没有证明 production path 的非默认值真正到达最终 consumer。

## 怎样修复

最终保持两个明确产物，而不是恢复完整 request compiler：

```text
root + nested request sources
        ↓
当前 RFC slice 的 duplicate / alias validation
        ↓
normalized model extra_args + bounded diffusion_request_args consumer view
        ↓
既有 pure / mixed dispatcher
        ↓
prompt / AR metadata / diffusion sampling params
```

- Consumer view 只包含 common diffusion fields、既有 service controls 和 registry 中不与它们重叠的 declared fields；unknown raw payload 不透传。
- Registry-declared fields 先减去 common/control owner；重叠字段仍参与跨来源冲突检查，但只进入一个 consumer。
- Pure、mixed 和 AR sampling 只消费 validated view，不再读取 `request.extra_body` 或 `model_extra` 来重建来源策略。
- `sampling_params_list`、topology、model capability 和 YAML defaults 保留原 owner；PR1 不为它们建立新 compiler。

## 测试怎样做减法

用同一类真实请求覆盖两个 dispatcher：

```text
root controls: num_inference_steps + size + negative_prompt + modalities
nested canonical extras: extra_body.extra_args
        ×
pure / mixed
        ↓
final prompt + AR target_h/target_w + diffusion sampling params
```

当尺寸注入从 `_apply_request_overrides` 移到 validated dispatcher path 后，删除只证明旧 helper 内部行为的重复测试。保留尺寸 parser 单测、duplicate/alias 合同测试和最终 consumer 集成测试。测试减法的验收是“owner 行为仍有唯一覆盖 + 测试路径净减少”，不是只看参数化形式或 case 数量。

## 下次怎样提前阻止

1. 写 RFC slice 的一句话目标和明确 out-of-scope 列表；single owner 不得扩大这份列表。
2. 修改前搜索所有 `request.extra_body`、`model_extra` 和 `nested or root` 读取，画到最终 prompt、control 和 sampling consumer。
3. 先写一条 root control + nested extras 的真实请求回归，让它经过每个受影响 dispatcher。
4. 第二个 finding 再次指向同一 owner 时停止逐字段修补，重新检查 scope，而不是默认升级成完整 compiler。
5. 编辑阶段只跑最小 targeted test；diff 冻结后跑一次完整 focused suite；最后才让 sub-agent 审查当前最终 diff。
6. 职责迁移时删除旧 helper 测试，用最终 consumer 覆盖接管，不以新增测试数量证明正确性。

## 相关资料

- PR：`vllm-project/vllm-omni#5171`
- 已提炼规则：[Serving 请求合同规则](../rules.md)
- 稳定数据流：[Serving 共享架构](../architecture.md)
- 通用来源矩阵：[Review execution contract](../../../../../framework/review/guides/review-execution-contract.md#source-consumer-decision-matrix)
- 复盘分流：[Retrospective to rules](../../../../../framework/debug/guides/retrospective-to-rules.md)
