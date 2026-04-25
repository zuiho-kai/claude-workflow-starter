---
name: Version Compatibility on Remote Server
description: 远端服务器 vllm/numpy/cv2 版本兼容性问题及解决方案
type: project
---

## 远端版本兼容问题（2026-04-14，已解决）

### 环境
- 容器 `<YOUR_CONTAINER>`（docker exec -it <YOUR_CONTAINER> bash）
- 系统 Python：`/usr/local/lib/python3.12/dist-packages/` → vllm 0.18.0
- venv：`<YOUR_REMOTE_WORKDIR>/.venv/` → vllm 0.19.0

### 解决方案
激活 venv 即可：
```bash
source <YOUR_REMOTE_WORKDIR>/.venv/bin/activate
```
venv 里 vllm 0.19.0 和 vllm-omni 0.19.0rc2 API 兼容。

### numpy/cv2 冲突
cv2 编译时用 NumPy 1.x，但远端装了 NumPy 2.2.6。pytest conftest.py 会 import cv2 导致 ImportError。
解决：`pip install "numpy<2"`。

**Why:** 不激活 venv 会用系统 vllm 0.18.0，API 名字不兼容（TokenInputs vs TokensInput 等）。
**How to apply:** 远端跑任何 vllm-omni 相关脚本前，先 `source <YOUR_REMOTE_WORKDIR>/.venv/bin/activate`。
