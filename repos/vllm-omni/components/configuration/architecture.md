# vLLM-Omni 配置构造架构

## 职责和边界

配置构造层负责把 pipeline/deploy、stage extras、CLI/runtime overrides、默认 factory 和 direct kwargs 转成有明确 owner 的最终配置。它不负责模型算法、服务层请求限制或 orchestrator 专属开关；这些字段只能在各自 owner 的边界消费，不能因为经过同一个字典就进入 diffusion config。

严格校验不是新的总 owner。稳定边界固定分为四层：

1. **来源合并与归一化**：保留来源优先级，处理 alias、flat→nested、可转换标量和兼容路由。
2. **ownership validation**：只判断规范化后的 key 是否属于 shared、stage、diffusion 或明确的 compatibility owner。
3. **按 owner 分区**：校验通过后才把 shared engine args、stage config 和 diffusion payload 分开。
4. **构造最终对象**：typed projection、legacy config 和 direct factory 不再重新解释来源或静默过滤字段。

## 主要源码和调用入口

当前主要入口以目标 checkout 的 live 源码为准，职责关系如下：

- `vllm_omni/config/stage_config.py`：pipeline-wide 与 stage-local overlay、默认值和 stage extras。
- `vllm_omni/engine/arg_utils.py`：CLI 字段 owner、orchestrator/shared/per-stage 路由集合。
- `vllm_omni/diffusion/data.py`：diffusion alias、quantization、parallel normalization 和共享 strict validator。
- `vllm_omni/config/omni_config.py`：structured 构造、shared engine args 分区和 typed diffusion projection。
- `vllm_omni/engine/stage_init_utils.py`：legacy startup 的 strict partition。
- `vllm_omni/engine/async_omni_engine.py`：默认 single-stage diffusion factory 和 schema 驱动的 passthrough。

## 数据怎样流动

```text
pipeline / deploy / engine_extras / CLI
                  |
                  v
       stage overlay 与优先级合并
                  |
                  +---------------- structured -----------------+
                  |                                              |
                  |                                   shared normalization
                  |                                              |
                  |                                   full-key validation
                  |                                              |
                  |                           shared args --------+-------- diffusion projection
                  |                                              |
                  +---------------- legacy startup --------------+
                                                                 |
                                                      diffusion-only payload
                                                                 |
                                                OmniDiffusionConfig.from_kwargs

default single-stage factory -> schema-declared passthrough -> legacy startup
direct kwargs ---------------------------------------> direct normalize + strict validate
```

structured 与 legacy 可以有不同的最终对象，但不能有不同的字段语义。它们必须在第一位 consumer 前共享 normalization 和 full-key validation；差异只允许发生在校验之后的 typed projection 或对象构造。

## 值状态合同

| 状态 | 必须怎样处理 |
|---|---|
| key 缺失 | 使用 owner 声明的默认值 |
| 已知 key 为 `None` | 只有该 source/overlay owner 明确声明 unset 语义时才丢弃 |
| 已知 key 为 `False` 或 `0` | 作为显式值保留，不能用 truthiness fallback 覆盖 |
| 未知 key 为 `None` | 仍然是 unknown field，不能在校验前过滤 |
| legacy 非空、canonical 为 `None` | canonical 视为 unset，可提升 legacy 值 |
| legacy 与 canonical 都非空 | 按同一 owner 的冲突合同拒绝 |

## 默认 factory 与 schema

默认 factory 是公开配置入口，不是可以长期维护第二份字段白名单的捷径。只有明确标记为可序列化 passthrough 的 schema 字段才进入 stage engine args；不可序列化的 runtime object 保留在 metadata，service/orchestrator 字段留在各自 owner。

上游新增字段或 rebase 后，必须重新核对：

1. 字段属于 pipeline、stage、shared engine、diffusion、service 还是 orchestrator；
2. 是否需要 structured projection、legacy partition、direct factory 或默认 factory 支持；
3. `None`、显式 falsey 值和冲突值的语义；
4. 自动合并是否漏掉 owner 集合、derived field 或 passthrough metadata。

## 怎样验证

1. 从每个受影响真实入口走到第一位 consumer，再断言最终 config 或明确错误。
2. 使用“案例 × 入口”参数化矩阵证明 structured、legacy 和 direct 行为一致；另保留默认 factory 与一个未受影响 stage 类型作为 control。
3. 严格错误必须覆盖 unknown non-null 和 unknown `None`；兼容路径必须覆盖 canonical `None`、双非空冲突和显式 `False`。
4. rebase 后在最新 base 上重新运行语义测试，并把自动合并文件作为新 diff 审查；lint、compile、mergeable 或旧 head 的绿测不能代替。
