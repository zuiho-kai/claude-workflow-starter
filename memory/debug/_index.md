# Memory · debug/

**何时来翻**：调试 vllm-omni 跨组件问题（AR↔DiT 桥接、attention mask、版本兼容）。和具体模型解耦的通用知识。

| 文件 | 一句话 |
|------|--------|
| [ar_dit_bridge.md](ar_dit_bridge.md) | AR→DiT 数据桥接：传 `cot_text` 而非 raw token IDs |
| [bidirectional_attention.md](bidirectional_attention.md) | 图像 token 双向注意力：需加 `is_mm_prefix_lm` |
| [version_compat.md](version_compat.md) | 远端 vllm/numpy/cv2 版本兼容问题 |
