# Error Book: 模型接入 & 精度对齐

## 2026-04-09 — Import — `hunyuan_image_3` 下划线命名残留
**症状**：`ModuleNotFoundError: No module named 'vllm_omni.diffusion.models.hunyuan_image_3'`
**根因**：上游 HF 用 `hunyuan_image_3`（带下划线），vllm-omni 用 `hunyuan_image3`，3 处 import 残留
**解法**：全部 `hunyuan_image_3` → `hunyuan_image3`
**提醒**：搬上游代码后 `grep -rn "hunyuan_image_3" vllm_omni/` 扫残留

## 2026-04-09 — HF 缓存 — base 权重下载不完整
**症状**：snapshot 只有 144K，blobs 有 `.incomplete` 文件
**根因**：下载 `tencent/HunyuanImage-3.0` 时中断
**解法**：改下 `tencent/HunyuanImage-3.0-Instruct`
**提醒**：base 和 Instruct 是两个不同 HF repo，partial download 不能互用

## 2026-04-09 — I2T — stage config 三个坑叠加
**症状**：`StageEngineCoreProc died during READY (exit code 1)`
**根因**：(1) modes 路由错误 (2) gpu_memory_utilization 太低 (3) GPU 被残留进程占用
**解法**：纯 LLM stage + `gpu_memory_utilization: 0.95` + 避开被占 GPU
**提醒**：I2T YAML 不要混 diffusion stage；AR TP4 每卡 ~41 GiB，utilization ≥ 0.9

## 2026-04-10 — T2T — 缺 `__name__` 保护导致子进程崩溃
**症状**：`StageEngineCoreProc died during HELLO`，logical IDs exceed visible devices
**根因**：spawn 模式重新导入主脚本，没有 `__name__` 保护时子进程又创建 `Omni()`
**解法**：加 `if __name__ == "__main__":` 保护
**提醒**：任何调用 vLLM-Omni 的脚本必须有此保护

## 2026-04-10 — AR 精度 — sampling 参数改后空输出
**症状**：sampling 模式下只生成 `</answer><|endoftext|>` 两个 token
**根因**：缺官方的 `_StageTransitionLogitsProcessor` 和 `_ConditionalSliceVocabLogitsProcessor`
**解法**：实现自定义 `sample()` + `prefer_model_sampler = True`
**提醒**：AR 内部阶段转换（think→recaption→ratio）靠 logits processor，不是 orchestrator

## 2026-04-10 — 官方对比 — load_tokenizer 缺 model_version
**症状**：`AttributeError: 'HunyuanImage3Config' object has no attribute 'model_version'`
**解法**：用 importlib 从模型 package 导入 tokenizer 类，不传 `model_version`
**提醒**：官方代码假设 config 有的字段，HF hub config.json 不一定有

## 2026-04-10 — 精度对比 — prompt template 不一致
**症状**：同一 prompt 文本输出 0% 匹配
**根因**：官方用 `apply_chat_template()` 构建 prompt，vLLM 用 `build_prompt()`，结构不同
**解法**：dump 官方 `input_ids`，直接喂给 vLLM
**提醒**：精度对比必须用完全相同的 input_ids

## 2026-04-10 — T2I AR — ratio token 死循环
**症状**：ratio token 无限循环直到 max_tokens
**根因**：`_apply_ratio_restriction` 只在 `last_token == size_token_id` 时触发，选了 ratio 后不再触发
**解法**：`last_token in self._all_ratio_ids` 时强制输出 EOS
**提醒**：官方 ratio tokens 是 `final_stop_tokens`，vLLM `stop_token_ids` 不包含它们

## 2026-04-10 — bf16 greedy 下跨框架 token 分歧
**症状**：前 122 token 一致，pos 122 开始分叉
**结论**：不是 bug。bf16 + 不同算子 → 浮点累积误差。前几百 token 一致就算对齐成功
