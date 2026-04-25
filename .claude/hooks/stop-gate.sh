#!/usr/bin/env bash
# stop-gate.sh — Stop hook 综合门禁
#   1. 检测本轮有代码改动 → 提醒去远端跑测试
#   2. 检测本轮有实际工具执行失败 → 提醒写 error book / memory

input=$(cat)
transcript_path=$(printf '%s' "$input" | grep -oE '"transcript_path"[[:space:]]*:[[:space:]]*"[^"]+"' | sed -E 's/.*"([^"]+)"$/\1/')

if [[ -z "$transcript_path" || ! -f "$transcript_path" ]]; then
    exit 0
fi

last=$(tail -n 400 "$transcript_path" 2>/dev/null)
if [[ -z "$last" ]]; then
    exit 0
fi

has_code_change=false
has_tool_failure=false

if echo "$last" | grep -qE '"name"[[:space:]]*:[[:space:]]*"(Edit|Write|NotebookEdit)"'; then
    has_code_change=true
fi

# 只匹配实际工具执行失败的强信号（Python 栈回溯、GPU OOM、测试框架 FAIL 输出）
# 不匹配对话中讨论错误的弱信号
if echo "$last" | grep -qE '(Traceback \(most recent call last\)|CUDA out of memory|OOM|pytest.*FAILED|AssertionError|"exit_code"[[:space:]]*:[[:space:]]*[1-9])'; then
    has_tool_failure=true
fi

if ! $has_code_change && ! $has_tool_failure; then
    exit 0
fi

msg="📡 本轮总结："

if $has_code_change; then
    msg="${msg}\\n• 检测到代码改动 → 建议去远端服务器跑测试验证：按 docs/remote_server.md 走 SSH+tmux+docker，启动前三连（GPU/模型路径/缓存变量），跑完三步释放（pkill→exit 容器→exit srun）。"
fi

if $has_tool_failure; then
    msg="${msg}\\n• 检测到工具执行失败 → 用 /claudeception 自动提炼到 .claude_errors/（踩坑）或 memory/（常识），或手动按格式追加。重复 ≥2 次的坑 → 升级到 CLAUDE.md 硬规则区。"
fi

msg="${msg}\\n\\n回 'skip' 跳过。"

printf '{"systemMessage": "%s"}\n' "$msg"

exit 0
