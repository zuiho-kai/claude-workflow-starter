---
name: Official I2T Baseline Output
description: 官方 HF 模型 I2T 推理的 baseline 输出，用于和 vLLM-Omni 对比
type: project
---

## Official I2T Baseline（2026-04-14，已更新）

测试图片：`test_scene.png`（简单几何图形：蓝色背景、黄色椭圆、绿色矩形、棕色小矩形）
Prompt：`Describe the content of the picture.`
模式：greedy（do_sample=False），bot_task=auto，bf16，4×H800，SDPA

### 最新 baseline（固定 device_map）
- 638 tokens（device_map 保存在 `/scratch/<YOUR_GROUP>/<YOUR_USERNAME>/fixed_device_map.json`）
- 输出文本开头：`The image displays a simple, abstract composition featuring a light blue background. Centered in the upper half is a solid yellow oval. Below the oval, a green rectangular block spans horizontally across the image...`

### 跨进程确定性测试结论
1. **同进程内 greedy 完全确定**：两次 generate 输出 466 tokens 完全一致（aligned_test3 验证）
2. **跨进程即使固定 device_map 仍有分歧**：baseline 638 tokens vs verify 458 tokens，前 34 tokens 一致后分歧
3. **根因**：bf16 多卡推理时 NCCL all-reduce 浮点累加顺序、CUDA kernel 非确定性。greedy argmax 在 logits 接近时对微小数值差异敏感
4. **结论**：这是 PyTorch 多卡 bf16 推理的固有行为，不是代码 bug。对 vLLM-Omni 对齐验证不能依赖 token 级精确匹配

### 对齐验证标准
- input_ids 完全一致 ✓（6364 tokens）
- 输出语义一致、结构合理（描述内容正确）
- 前 30+ tokens 一致（greedy 分歧点在合理范围内）

### 文件位置
- 远端 baseline JSON：`/scratch/<YOUR_GROUP>/<YOUR_USERNAME>/official_i2t.json`（最新，含固定 device_map 下的 output）
- 远端 device_map：`/scratch/<YOUR_GROUP>/<YOUR_USERNAME>/fixed_device_map.json`
- 测试脚本：`/scratch/<YOUR_GROUP>/<YOUR_USERNAME>/aligned_test4.py`（baseline/verify 两模式）

**Why:** 这是对比 vLLM-Omni 输出正确性的 ground truth。
**How to apply:** vLLM-Omni 对齐验证看 input_ids 精确匹配 + 输出语义一致 + 前 30 tokens 匹配，不要求 token 级完全一致。
