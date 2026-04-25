---
name: Follow User Instructions Immediately
description: 用户明确给出方案时，直接执行，不要先试自己的方案再回头
type: feedback
originSessionId: 4cc65e60-2b58-4a9f-9d4e-5bd1dffdc6b7
---
用户说"减层跑"时，直接减层。不要先试不减层的方案再 OOM 回来。

**Why:** 用户说了 TP=2 + 减层，我先试了 TP=2 不减层，OOM 后才减层，浪费了一轮远端调试时间（2026-04-21）。远端机器时间宝贵，每轮 serve 启动+失败要几分钟。

**How to apply:** 用户给出明确技术方案时，直接执行。不要"先试试不改看行不行"。用户比你更了解模型和硬件约束。
