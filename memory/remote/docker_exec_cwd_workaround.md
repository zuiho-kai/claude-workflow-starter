---
name: Docker exec permission workaround
description: docker exec 报 chdir permission denied 时，先 cd 到容器 cwd 对应的宿主路径再 exec -it
type: feedback
---

docker exec 容器时如果报 `chdir to cwd ("...") set in config.json failed: permission denied`，解法是先在宿主机 `cd` 到容器配置的工作目录路径，再 `docker exec -it`。

**Why:** 容器的 config.json 里设了 cwd（如 `/scratch/<YOUR_GROUP>/<YOUR_USERNAME>/workdir`），非交互式 exec 在权限不足时直接失败。先 cd 到对应宿主路径 + 用 `-it` 交互模式可以绕过。

**How to apply:** 遇到 docker exec permission denied 时：
```bash
cd /path/matching/container/cwd && docker exec -it <container> bash
```
不要用 `docker exec -w /tmp` 之类的 workaround（虽然能跑单条命令，但不适合交互式操作）。
