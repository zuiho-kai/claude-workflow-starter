# Error Book: PR Review 反馈

## 2026-04-15 — 硬编码 EOS token ID
**症状**：reviewer 指出 `self._eos_token_id: int = 127957` 是硬编码
**解法**：改为 `tokenizer.eos_token_id`
**提醒**：永远不要硬编码 token ID，从 tokenizer 对象动态获取

## 2026-04-15 — _clear_transition_state 定义但未调用
**症状**：`_transition_state` dict 会随请求累积
**解法**：`decoded_tokens` 为空时调用 `_clear_transition_state(req_idx)`
**提醒**：写了清理方法就必须同时写调用点

## 2026-04-15 — patch.py 死代码未清理
**症状**：`if _orig_cp is not _patched_cp: pass` 是死代码
**解法**：删除空分支
**提醒**：提交前搜索 `pass` 和 `# just in case`

## 2026-04-16 — sample() 暗示 batch 支持但实际不支持
**症状**：`for req_idx in range(logits.shape[0])` 暗示支持多请求
**解法**：加 `assert logits.shape[0] == 1`
**提醒**：只支持特定约束时用 assert 显式声明

## 2026-04-16 — patch.py monkey patch 静默失效风险
**症状**：上游改实现后 patch 可能静默不生效
**解法**：patch 后立即 assert 验证 `_installed is _patched_cp`
**提醒**：monkey patch 必须有 import-time sanity check

## 2026-04-16 — _apply_ratio_restriction 测试误解 greedy 行为
**症状**：断言所有 ratio token logits ≠ min_score，但方法后半段做了 argmax + 再次 fill
**解法**：改为 `test_greedy_selects_single_ratio_token` + `test_extra_ratio_slices_considered`
**提醒**：写测试前必须读完整个方法，特别注意 in-place mutation

## 2026-04-16 — test 引用不存在的 YAML
**症状**：reviewer 指出 `hunyuan_image3_t2i.yaml` 不在本 PR 中
**解法**：说明该文件已随 #2712 合入 main
**提醒**：PR 依赖其他 PR 的文件时，在 description 注明依赖关系

## 2026-04-16 — image/images 双格式处理
**症状**：reviewer 问 `if pil_image is not None:` 能否用 `else`
**解法**：说明两个 `get` 都可能返回 None，参考 `glm_image.py` pattern
**提醒**：multimodal data key 不统一（`image` vs `images`），要同时处理

## 2026-04-16 — _get_forced_token O(n²) 复杂度
**症状**：每个 decode step 倒扫整个 `decoded_tokens`
**解法**：acknowledge，当前长度有界（T2I ~900, I2T ~2048），可忽略
**提醒**：序列 >10K tokens 时需改为缓存 trigger position 的增量方案
