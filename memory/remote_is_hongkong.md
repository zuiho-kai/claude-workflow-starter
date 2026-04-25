---
name: This cluster is in Hong Kong, use default PyPI (not tsinghua)
description: 远端是香港机器，直连 pypi.org 快；绕路清华反而慢
type: rule
---

# 远端 远端节点 是香港机器

## 规则

- **默认 PyPI 直连**：`pypi.org` 连得很快
- **不要用清华源**：`pypi.tuna.tsinghua.edu.cn` 在香港机器上**反而慢**（香港 → 北京 → 清华 → 香港，反向绕路）
- **不要用阿里云源**：同理

## 容器里 pip 配置可能是遗留

`pip config list` 如果显示 `global.index-url='https://pypi.tuna.tsinghua.edu.cn/simple'`，那是镜像拉自国内集群的老配置遗留，**在香港节点上应当无视或覆盖**：

```bash
# 好：直连 pypi
uv pip install --index-strategy unsafe-best-match <pkg>
pip install --index-url https://pypi.org/simple <pkg>

# 坏：绕路清华
uv pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple <pkg>
pip install <pkg>  # 如果 pip.conf 是清华
```

## 数据点

- 装 `mmengine`：清华源挂起 60+ 秒不动 → Ctrl-C；默认 pypi **3.82 秒** 装完
- 装 `open_clip_torch + clip-benchmark`（5 个包）：默认 pypi ~20 秒

## 踩坑教训：装包慢先怀疑源，不要怀疑包

**症状**：`uv pip install X` 卡 60 秒无输出，我以为是 uv 在解依赖
**真相**：是 pypi.tuna 清华源在香港连接慢；切 pypi.org 3.82 秒完成
**教训**：命令行装包不动，第一反应**换源**（pypi.org），不要去 Ctrl-C 然后换工具（pip vs uv）——**工具不是问题，源才是问题**

## Docker image 里的 pip.conf 是遗留

`pip config list` 在镜像里如果显示清华源，是因为这个 docker image 是在国内集群里构建的。**在香港/海外节点上是反向绕路**，必须覆盖：

```bash
# 好：--index-url 显式覆盖
uv pip install --index-strategy unsafe-best-match X  # uv 不读 pip.conf，默认 pypi.org
pip install --index-url https://pypi.org/simple X    # pip 读 pip.conf，要显式覆盖

# 不要依赖 pip.conf 默认值，因为它可能是清华
```

## 推论

- HF 下载同理，`hf download` 默认直连 `huggingface.co`，在香港直连最快，不要设镜像
- `apt install` 同理，默认 `archive.ubuntu.com` 或 docker image 预设的源通常 OK
