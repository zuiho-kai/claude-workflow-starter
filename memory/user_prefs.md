---
name: User Working Style Preferences
description: 用户偏好快速执行、不喜欢重复分析已知问题
type: feedback
---

不要花大量时间重复分析已经发现过的问题。如果之前对话中已经得出结论，直接用结论推进，不要重新验证。

**Why:** 用户明确表达过不满："为什么耗时那么久才分析出这种最简单的东西，这个之前不是已经发现过了么"
**How to apply:** 优先行动，减少分析循环。已知结论直接应用，不要重新推导。遇到问题快速修复，不要反复确认。

---

不要在确认脚本能跑之前就 sleep 等待。先快速验证脚本已经启动（检查 tmux 输出），确认没有立即报错，再 sleep 等结果。

**Why:** 用户明确说过："你先别sleep，你确认能跑再sleep"。之前多次出现 sleep 等了几分钟结果脚本根本没上传成功或路径错误的情况。
**How to apply:** 远端执行脚本后，立即（不 sleep）检查一次 tmux 输出，确认脚本已开始运行且没有立即报错，然后再 sleep 等待结果。

## 具体操作模板（不要再违反）

**错误示范**（2026-04-21 犯过两次）：
```
send-keys pytest ...
sleep 5  ← 太短，只看到命令行回显没看到任何执行进度
capture pane（没报错，pytest 才刚启动）
sleep 150  ← 违反规则：还没确认 pytest 真正 collecting/running 就长 sleep
```

**正确做法**：
```
send-keys pytest ...
sleep 3-5
capture pane
检查 capture 输出里有没有以下任一：
  - pytest 的 "collected N items"
  - pytest 的 "PASSED" / "FAILED"
  - 我关心的程序日志（比如 "Launching OmniServer"、"[logo.py:45]"、"Loading weights"）
  - 明确的错误信息（Traceback / unrecognized arguments / ModuleNotFoundError）
看到任一，才允许 sleep 长时间等下一个阶段。
都没看到（光是 prompt 回显 / 静默），说明命令可能没真正进入执行，重查 send-keys 是否被 shell 吞掉、quoting 是否对、cwd 是否对。
```

**绝对不允许**：「命令发了一次，看见回显就认为跑上了」。回显只证明 tmux 收到字符，不证明程序在执行。

---
